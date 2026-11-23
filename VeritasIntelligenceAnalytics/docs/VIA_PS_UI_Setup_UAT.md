# VIA PowerShell U/I + VCGC 4-指令中樞 — 安裝與前後 UAT 規劃

本頁是「進入 PowerShell 即進入 VIA 環境」的雙引擎(PS 現代化 TUI + Python Rich 矩陣)安裝與測試計畫。
**在正式寫入 `$PROFILE` 前,務必照四階段 UAT 走完**;容器內無 pwsh,以下實跑在你工作站。

## 檔案(兩支,路徑全用 `$PSScriptRoot` / `VIA_ROOT`,不含本機路徑)

| 檔案 | 角色 |
|---|---|
| `VCGC_CommandHub_v0100.py` | 全邏輯純 Python:4 指令 + Rich 矩陣 + 加速器橋(生效載入)+ 自動降級(無 Rich 也不報錯) |
| `VIA_ProfileLoader_v0100.ps1` | 薄層 TUI 外殼:進環境 + 選擇題 / 直接貼上雙軌;交給操作員的 PS 只有這一支 |

## 四個短指令(由 ~9 支舊指令收斂;舊指令保留別名向下相容)

| 短指令 | 功能 | 引擎 |
|---|---|---|
| `via` | 主控台:晨間讀前次備份 + 頂部短指令矩陣 + 系統摘要;選擇題或按 Enter 直接貼上 | PS UI + Rich |
| `via-pano` | 全景檢視 GitHub + 本機 PC File,一輪安全 AST 修復(**預設乾跑**,`-Apply` 才寫) | Python AST/CST |
| `via-bak` | 主動備份快照 + Graphify 拓撲 + OmniRoute 帳本 + agency-mem 交接記憶(SHA-256) | 純 Python |
| `via-ast` | AST 導入加速器:剪貼簿 / `-CodeFile` / `-Code`,**diff 預覽 + 確認**,`-Rollback` 還原 | ast + compile 沙盒 |

## 前置安裝(工作站,只做一次)

```powershell
Install-Module -Name PwshSpectreConsole -Scope CurrentUser -Force   # 現代化 TUI(可選;無則自動降級)
pip install rich libcst --upgrade                                     # Rich 矩陣 + libcst(保留註解的 AST 修復)
```

> 無 `rich` → Python 自動降級為純文字矩陣,不報錯。無 `libcst` → `via-pano` 退回 `ast`(會重排版、丟註解),故建議裝 libcst。

## UAT 四階段(全綠才可寫 `$PROFILE`)

**Phase 1 — 依賴與編碼隔離**(不改系統設定)
```powershell
pwsh -NoProfile -Command "Import-Module PwshSpectreConsole; python -c 'import rich,libcst;print(\"OK\")'"
# 另:確認本檔可被 PS 剖析(語法閘)
pwsh -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw .\VIA_ProfileLoader_v0100.ps1)); 'PS parse OK'"
```

**Phase 2 — Python 引擎沙盒壓測**(不經 PS,直接驗 4 指令與矩陣不折行破圖)
```powershell
$env:VIA_ROOT = (Get-Location).Path
python .\VCGC_CommandHub_v0100.py boot
python .\VCGC_CommandHub_v0100.py pano                 # 乾跑,不寫檔
python .\VCGC_CommandHub_v0100.py bak --note "UAT測試"
```

**Phase 3 — PS 雙軌互動與 AST 加速驗收**(沙盒視窗,`-NoProfile` 不汙染環境)
```powershell
pwsh -NoProfile -File .\VIA_ProfileLoader_v0100.ps1
# 驗:① 按 Enter 進原生列、貼多行指令不閃爍不截斷
#     ② 輸入 via 重開選單;選 4 以剪貼簿注入測試函式 → 確認 diff 預覽出現、確認後才寫
#     ③ via-ast -Target <檔> -Rollback 可還原最近一次注入
```

**Phase 4 — 寫入 `$PROFILE` + 逃生閥**(前三階段全綠才做)
```powershell
if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
Add-Content -Path $PROFILE -Encoding UTF8 -Value @'

# --- VIA VCGC 現代化雙引擎預設啟動 ---
$ViaLoader = Join-Path $env:VIA_ROOT 'VIA_ProfileLoader_v0100.ps1'
if ($env:VIA_ROOT -and (Test-Path $ViaLoader)) { . $ViaLoader }
'@
# 寫入前先設好 $env:VIA_ROOT 指向 VIA 根(或把上面那行改成你的實際根目錄判斷)
```

**逃生閥**:任何套件更新導致啟動異常時,`pwsh -NoProfile` 一鍵進純淨終端機修復;本外殼有 `Test-Path` 防呆,檔案遺失不報錯。

## 安全與治理對齊

- **加速器 100% 生效**:Python 入口帶 `[VIA:ACCEL-BRIDGE]`,實測從 VIA 根可載入 `VIA_SuperAccel_Module`(非只標記)。
- **AST 注入先沙盒**:一律 `ast.parse` + `compile()` 過才落檔,並留 `.astbak`;`via-ast -Rollback` 可還原。
- **不寫死本機路徑**:路徑全由 `$PSScriptRoot` / `$env:VIA_ROOT` 決定;狀態與備份寫在 `VIA_Reports/vcgc_hub/`(.gitignore 已排除,永不入庫)。
- **PS 只一支**:只負責進環境與呼叫 Python;出新版時同一則回覆點名作廢舊版。

## v0101 更新(2026-11-23)· **v0100 作廢**,改用 `VIA_ProfileLoader_v0101.ps1`

新增兩個指令(選單第 5、6 項):

| 指令 | 做什麼 | 安全設計 |
|---|---|---|
| `via-auth` | 看授權狀態;`via-auth -Fred` 以遮罩輸入 FRED key 存到 Windows **使用者層**環境變數;`via-auth -Clear` 移除 | 不寫任何檔、不進 git、只顯示末 4 碼;格式不符(非 32 位十六進位)不存 |
| `via-run` | 全線:VDF `launch --run` → VRN `VRN_MDL260 run --source private\vrn_samples --via-db via_database`,各段計時 | 同意閘每次由你**當場輸入 YES**才開,只在本行程;`finally` 保證跑完或出錯都關閘;`-VdfOnly` / `-VrnOnly` 可分段 |

入口以檔名找尾版(`VDF_SystemManager_v*.py`、`VRN_MDL260_SafeParallelLaunch_v*.py`),桌機與倉兩種目錄結構都能用。

**`$PROFILE` 改成自動取最新版 loader**(以後出新版不用再改 profile):
```powershell
if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
Add-Content -Path $PROFILE -Encoding UTF8 -Value @'

# --- VIA VCGC 現代化雙引擎預設啟動(自動取最新版 loader)---
if ($env:VIA_ROOT) {
    $ViaLoader = Get-ChildItem $env:VIA_ROOT -Filter 'VIA_ProfileLoader_v*.ps1' -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if ($ViaLoader) { . $ViaLoader.FullName }
}
'@
[Environment]::SetEnvironmentVariable('VIA_ROOT', '<你的 VIA 根目錄>', 'User')   # 只需設一次
```

**v0101 UAT 追加**(在 Phase 3 沙盒視窗內):
1. `pwsh -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw .\VIA_ProfileLoader_v0101.ps1)) | Out-Null; 'PS parse OK'"`
2. `via-auth` → 只看狀態(不輸入 key),確認顯示「未設定 / 已設定(…末4碼)」。
3. `via-auth -Fred` → 貼 key → 再跑 `via-auth`,使用者層與本視窗都顯示已設定。
4. `via-run` → 看計畫列出 VDF/VRN 入口與路徑 → **輸入 NO**,確認「未擷取」且 `$env:VIA_NET_CONSENT` 為空。
5. 真跑:`via-run` 輸入 YES;結束後 `$env:VIA_NET_CONSENT` 應為空(閘已關)。


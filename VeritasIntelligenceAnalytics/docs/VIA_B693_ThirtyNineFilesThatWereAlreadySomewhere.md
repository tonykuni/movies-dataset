# 批693 · 側枝 39 件,量完一件新料都沒有:25 件是已收包的上一代,13 件是姊妹倉 965504f 的原字節

> 本線=VRN 線(分支 `claude/vrn-line-b691`,自 main d520d9f3 重起)。批號 693 取號前掃過全部遠端分支(LL334):692 已由本線併進 main(PR #69);母線 awesome-bardeen 未併的 a1ff0d82/825efa10/cfae3a34 也自稱 批692,依律後到的加 B(請它改 692B)。
> 本批文件件,不動引擎、不動冊;側枝原件零觸碰(L03/L25)。

來件:母線 2026-09-21 17:54Z 轉交——操作員照 L25 把工作站未追蹤的 VRN 件推到側枝 `origin/local/parallel-b692`(bee8a683,基底=母線 825efa10;`git diff --name-status origin/main` 裡的 D 兩筆只是基底舊,不是真刪)。39 件 · 39,866 行。

## 一 · 逐件對表(LF 正規化後 md5;工作站件帶 CRLF,README 一檔就有 95 個 \r——LL(批546)同一課)

| 夾 | 件 | 對到誰 | 判 |
|---|---|---|---|
| `references/intake/VIA_SSOT_Additive_Audit_v0100/`(25 件) | 24 件 + `_upload/VIA_SSOT_Additive_Audit_v0100_2.zip` | **主線已有** `…_v0100_b20260921/`(31 件;S20260921 文收的 `VIA_SSOT_Additive_Audit_v0100.zip`,content_version 0.2.0,baseline 8e8e766f)。LF 後 21 件位元相同;4 件不同(`DELIVERY_MANIFEST` 4131 vs 4940 B · `README` 8657 vs 8974 · `SYNONYM_LIBRARY.json` 158,664 vs 172,418 · `audit_ssot.py` 25,010 vs 25,412)——側枝這份是**更早一代**(S20260921 文四節早已判定:`_2.zip` 是 v0.2.0 之前的版本,不收第二份);主線那份還多 6 件(VRN_Evidence_Core.py / WORKFLOW_EXTENSION / QA / SPEC.md / test_vrn_evidence.py / 收容 manifest) | **不收**(已收的是較新一代;第二份=第二本冊) |
| `knowledge/SYNONYM_LIBRARY_v3.json` | 152,899 B · md5 37b97f48 | = 側枝那份舊包裡的 `SYNONYM_LIBRARY.json`(位元相同) | 零新詞,不收 |
| `knowledge/SYNONYM_LIBRARY_v4.json` | 172,418 B · md5 4a946821 | = **主線 `_b20260921/SYNONYM_LIBRARY.json`**(位元相同;樞紐 v0112 `additive` 與 MDL176 早已在讀它,批689B 只增不減先證過) | 零新詞,不收;不必再過 MDL176 |
| `knowledge/VRN_WORKFLOW_SPEC_v0200.md` | md5 96ee2a83 | = 姊妹倉 965504f 同名件 | 姊妹倉件 |
| `engine/VRN_PanoramaProbe.py` | md5 e83d1a1f | = 姊妹倉 **965504f**(不是膠囊那版 c1989e6 be476237) | Z109 那一題,原封不動 |
| `engine/VRN_AutoTestLoop.py` · `engine/VIA_TW_Ticker_Master_v0210.py` · `tests/test_VRN_*.py` ×4 · `Invoke-VRN-AutoTest.ps1` | 4a2a119b · d76de330 · 46e86a07/b1451392/549a354a/5e5220b3 · a32d04d1 | 全部 = 姊妹倉 965504f 同路徑件 | 姊妹倉件 |
| `engine/VIA_VRN_FirstPageEngine.py`(無版號) | 79,155 B · md5 64e08bc9 | = 姊妹倉 965504f;檔頭自稱「VIA_VRN_FirstPageEngine v0102 ALL-IN-ONE」——**與母樹的 VIA_VRN_FirstPageEngine_v0102(73,342 B)不是同一支**,母樹尾版是 v0127 | **第二血統的首頁引擎**;落進母樹 = 九頭龍(L05),不收 |
| `engine/VRN_Integrated_ReportDatabase_Engine.py` | 110,296 B · md5 44f152f1 | 母樹 intake `…_b685/`(78,094 B · 58120333,批685 逐函式對映進 FieldRules_SSOT/ENG074 的那支)是**舊一代**;側枝這份 = 姊妹倉 965504f 的新一代 | 新一代比 b685 多 32 KB;要不要重做對映=你裁(Z117) |

**結論**:39 件裡零件是「只有這裡有」的新料。13 件姊妹倉件的正典家在姊妹倉(965504f 已推),側枝 bee8a683 也留著原字節(L25);母樹不再放第三份。

## 二 · 做了什麼

只有文件:本文 · 掉球 +Z117(側枝處置與兩題待裁)· 台帳一列。引擎零改、冊零改、側枝零觸碰。沒跑全格子(沒有件改;上一跑 v0445 OK 280 · FAIL 7 · SKIP 5 仍是現況)。

## 三 · 你的手

1. **Z117**:13 件姊妹倉件的處置——① 退回姊妹倉(母樹不收;側枝留檔)· ② 隨 Z109 一起裁:探針落地 ENG089 時只收探針一支,其餘仍留姊妹倉 · ③ 全收進 `references/intake/VIA_VDF_VRN_965504f_b693/`(原字節、零觸碰,只當對表用)。本線建議 ①。
2. **VRN_Integrated_ReportDatabase_Engine 新一代**(110 KB vs b685 78 KB):要不要把批685 的逐函式對映重做一次?要=一批的量。
3. 轉告母線:未併的三筆自稱 批692 的 commit 改 692B(本線 692 已先併 main)。
4. 其餘不變:Z114 登冊四件 · Z109 三選一 · Z91 · Z82 · Z88;`via-vrnrun` 那兩格。

## 四 · 一貼即用

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git checkout main; git pull origin main; git log --oneline -1
via-vrnrun
```

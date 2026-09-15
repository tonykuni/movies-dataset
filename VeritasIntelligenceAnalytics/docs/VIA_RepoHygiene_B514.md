# VIA 倉衛生 批514(中央治理家族歸位去重)

> 律:L23 只刪 byte 同(md5 同)且路徑/檔名未被程式引用的重複件;L30 相似功能整合只留一處;git 可回溯(4728252d 之前)

## 量到

- 操作員上傳五件(VIA_CentralGovernanceConsole.py · VIA_CentralGovernanceEngine.py · VIA_DownwardController.py · VIA_FilePriorityRouter.py · VIA_SameNameConsolidator_v0100.ps1)md5 與 `new modules engines/` 內 8 個 `(1)/(2)/(3)/(4)` 副本 **byte 全同**(批511 衛生報告已列為「另一條線引擎收容件,候下一批歸位」)。
- 這 8 個副本名只出現在批511 衛生報告與 b305 收容清單(紀錄),沒有任何程式以這些檔名呼叫(grep 全樹)。

## 歸位(正位一份,原名零觸碰)

`supportive modules/VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/` + `MANIFEST_b514.json`(md5 冊 · URN · 演進線 · 前身)。套件內互相以原檔名呼叫(DownwardController 能力冊),所以不改名;尾版律落在套件夾名 `_b5NN`。

## 刪(8 件;皆 byte 同於正位件)

| 路徑 | md5 | 正位件 |
|---|---|---|
| `new modules engines/VIA_CentralGovernanceConsole (2).py` | 1601e00906d2149813c380031b4411e2 | `VIA_CentralGovernanceConsole.py` |
| `new modules engines/VIA_CentralGovernanceEngine (2).py` | 2ff5be70058f70d78f52abad6507c14e | `VIA_CentralGovernanceEngine.py` |
| `new modules engines/VIA_DownwardController (2).py` | be4e42c15abcb9450682473b32ddc9e9 | `VIA_DownwardController.py` |
| `new modules engines/VIA_DownwardController (3).py` | be4e42c15abcb9450682473b32ddc9e9 | `VIA_DownwardController.py` |
| `new modules engines/VIA_DownwardController (4).py` | be4e42c15abcb9450682473b32ddc9e9 | `VIA_DownwardController.py` |
| `new modules engines/VIA_FilePriorityRouter (1).py` | 26ae51cc2aac0a9a44fa9b5b30e5db6d | `VIA_FilePriorityRouter.py` |
| `new modules engines/VIA_FilePriorityRouter (2).py` | 26ae51cc2aac0a9a44fa9b5b30e5db6d | `VIA_FilePriorityRouter.py` |
| `new modules engines/VIA_SameNameConsolidator_v0100 (1).ps1` | adf1bd7bd2c0f1c718785f760310297c | `VIA_SameNameConsolidator_v0100.ps1` |

## 不刪(誠實)

- `supportive modules/VIA_Central_Governance/CGC_MDL001_CentralGovernanceEngine_v0100..v0401.py`:同題演進線(語料 CLI),不是副本;深併候裁(掉球 Z24)。
- `new modules engines/VIA_CentralGovernance_ALL_v0100/`:AdaptiveDownstream 前身套件(含驗證證據),留作收容存證。

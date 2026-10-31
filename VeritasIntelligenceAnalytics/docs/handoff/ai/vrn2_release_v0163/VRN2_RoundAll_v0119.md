# VRN-2 一支 Python · VRN2_RoundAll_v0119.py(套件 v0163 · 不用 MOPS)

`VRN2_RoundAll_v0119.py`(只用 Python 標準庫 · SHA-256 `0960759c8c24`)= v0118 + 操作員 2026-10-31「不可用 MOPS · 全部國內使用 TWSE TPEX」:

| 改了什麼 | 說明 |
|---|---|
| 套件 v0163 | 啟動器 v0163:⑥e `--fetch` 一律 `--no-financial` · ⑥e 前把已落盤的 MOPS 財報移到 `_mops_quarantine`(不刪)· runtime v0156 原樣 |
| ④ 跑啟動器前 | 先移 MOPS 財報(啟動器也會做 · 先做不衝突)|
| ⑤ 自動修 | 有 MOPS 財報 → 移開 → 重抓價格(`--no-financial`)+ 重新填值 → ⑬b → Combined → 增量庫 → Workbench · ⑤ 重抓 ⑥e 也一律 `--no-financial` |

自測 74 項(v0118 的 72 項 + 73 ~ 74)。套件 `vrn2_release_v0163/VRN2_Closeout_v0163.zip`(SHA-256 `fd216929c5f1` · 本檔內已釘死)。**最省事:`VRN2_HandleAll_v0111.md`(cmd / PowerShell 各一段)**。

```bat
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0119.py" --only package,fix,report,closeout,pasteback
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0119.py"
```

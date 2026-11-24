# VIA 環境安裝規範 v1.1.0(八路衝突檢查 + 三鏡像 + 依計畫安裝)

v0100 → v0101:操作員 2026-11-24 兩則訊息定案(VCGC-REQ258;待登律號):

> 「更快先檢查經過衝突檢測三鏡像共同檢查衝突後環境確認無誤進行安裝計畫 依計畫安裝不用邊裝邊測 這個流程要寫入環境安裝規範」
>
> 「環境安裝規範為先檢查 base / via_core / via_ 開頭的環境全面檢視用 8 個檢測衝突的工具及清華阿里官方鏡像組成衝突檢查機制加入加速器
> 先檢查現在環境有無衝突，有衝突風險將風險移開立刻重建 在檢查無誤後 風險因子即沒裝的工具列入新增 特殊環境及分類一律單獨安裝
> numpy 這種常用允許多版本搭配 python 多版本共存 規劃環境安裝新增檢測無誤新增計畫 直接執行計畫無須再測」

v0100 的八路表、權威順序與存證規則照舊有效；本版改的是**順序**與**安裝方式**。

## 權威與入口

- 權威依序：Root SSOT → `VIA_EnvGovernance_Baseline_v0100.json`(家族 · 目標境 · 鏡像鏈 · 覆寫)→ `VIA_ToolRoster_SSOT_v0100.json` → EnvManager 白名單 → RunGate／LKGC。
- 操作員入口只有一行：`via-health`(VCGC 中樞 → `VIA_FastRun` 尾版)。安裝一律走 `via-install`(VCGC 中樞 → `CGC_MDL056_InstallGate` 尾版)；各境的單獨安裝走 `via-envgov`(`CGC_MDL135` / `CGC_MDL186`)。不直接 pip。
- 所有工具帶加速器橋(`[VIA:ACCEL-BRIDGE]`,語法樹真的匯入)；鏡像解析三道並行。網路同意閘只在安裝閘子行程裡設，不寫進任何檔。

## 流程(照順序；前一步不過，後一步不做)

| 步 | 做什麼 | 工具 | 過關條件 |
|---|---|---|---|
| ① 全面檢視 | base · `via_core` · 所有 `via_*` 境：八路檢查(下表)+ pip check + 多層 site 互撞 + 工具冊缺件 + 加速器 | `via-doctor`(envgov = 八路 · gate_conflict · gate_doctor · envtools · accel) | 無衝突風險 |
| ② 有風險 → 移開立刻重建 | pip check 有衝突，或 envgov / gate_conflict / gate_doctor 任一紅：**不新增**，把風險件移開、該境立刻重建 | `via-envgov plan` → `via-envgov apply --approve`(REBUILD 段;保留舊境與 LKGC) | 重建後回到 ①,直到無風險 |
| ③ 列新增 | 檢查無誤後，風險因子 = 沒裝的工具，列入新增 | doctor 計畫(`plan.pip`)· 工具冊缺件 | — |
| ④ 分流 | 特殊環境及分類一律單獨安裝：Baseline `package_env_overrides` / `families` 成員不進 base,列出目標境 | `via-install --plan-check`(自動分流) | base 計畫只剩一般件 |
| ⑤ 衝突檢測(三鏡像) | 清華 · 阿里 · 官方 PyPI 同時解析整份新增(零安裝);解不出 → 逐件找出剔除;鏡像版本不同 → 以官方為準;把解出的版本疊到現況推算「裝後新增衝突」;要從原始碼建置的件點名 | `via-install --plan-check` | 推算新增衝突 0;燈綠 / 黃 |
| ⑥ 新增計畫 | 寫計畫:全部釘版 · 參考鏡像 · 剔除 · 分流 · 推算結果 | `VIA_Reports/install_gate/PLANCHECK_latest.json` | 6 小時內 · 本機做的 |
| ⑦ 直接執行計畫 | 照計畫一次裝完(釘版、`--no-deps`,不讓 pip 臨場改計畫);**不再測**(⑤ 已測過)。只記帳(append-only `VIA_Lib_Registry`) | `via-install --from-plan` | rc 0 |

- 慢鏡像不拖整輪：第一個鏡像答完後，其他鏡像最多再等 max(90 秒, 4 倍)，逾時算沒回應(黃，不是綠)。
- 三個都連不到 = 灰(NOT_RUN)，不裝。推算有新增衝突 = 紅，不裝。

## 八路本機檢查(照 v0100)

| 路 | 本機判準 | 既有資料／免費工具 |
|---|---|---|
| 1 | BASE 與逐境解譯器身分、`pyvenv.cfg` | MDL135 identity scan |
| 2 | 原生 `.pyd` ABI 標籤與 Python 版本 | MDL135 native tag probe |
| 3 | 已安裝套件需求不滿足 | metadata／MDL135 `fast_check` |
| 4 | 同境重複發行版與路徑遮蔽 | `importlib.metadata`／MDL135 panorama |
| 5 | 第二條相依交叉檢查 | `python -m pip check` |
| 6 | 工具冊缺件、半拆件與重建段 | MDL135 tools plan |
| 7 | BASE 禁放家族與 `_M`／`_H` 獨占境 | Baseline families／工具冊 |
| 8 | 特殊語言執行檔、模型與支援工具 | roster external／PATH 探針 |
| +鏡像 | 待安裝全集解析，不寫入現況 | 清華 · 阿里 · 官方三鏡像 `pip install --dry-run --report`(安裝閘)；各境 `uv pip install --dry-run --python <該境解譯器>`(MDL186) |

## 多版本共存

- `numpy`、`pyarrow` 這類常用件**允許多版本**：不同 Python 版本、不同境各用各的版本(例：base 3.13 的 numpy 2.x 與 `via_iso_ml_cuda_H`(3.11)的 numpy 1.x 並存)。
- 封鎖的是**同一境**裡同名多版遮蔽或 ABI 錯配(八路第 2、4 路)；那是 ② 的風險，要重建。
- 家族境的 Python 版本照 Baseline `families.*.python`(例：ocr 3.13 · nlp 3.12 · deep_learning 3.11)。

## 存證

- 每輪 `via-health` 的全文在 `VIA_Reports/fastrun/<時間>/`(DOCTOR_before · PLANCHECK · 安裝紀錄);`--push` 只推雜湊與數字。
- 八路每跑照 v0100 存 `VIA_Reports/env_governance/eight_hub/`。`BLOCKED`、`NOT_RUN`、`REVIEW`、灰都不可當 PASS。

## 工作站一行

```powershell
via-health --push
```

只查不裝：`via-install --plan-check`;照最新計畫裝：`via-install --from-plan --yes`;各境單獨安裝:`via-envgov plan` → `via-envgov apply --approve`。

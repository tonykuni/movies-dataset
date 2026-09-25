# VIA 環境工具管理與八路衝突檢查政策 v1.0.0

## 權威與適用範圍

- 正式入口沿用 `scripts/VIA-Launch-Console.ps1` 註冊的 `via-envgov`；環境治理正典為 `CGC_MDL135_EnvGovernance_v0114.py`，本文件只提出附加檢查與執行規範，不另建中央 SSOT。
- 權威依序為 Root SSOT、`VIA_EnvGovernance_Baseline_v0100.json`、`VIA_ToolRoster_SSOT_v0100.json`、EnvManager 白名單及既有 RunGate／LKGC。政策變更只能透過 CGC Promote Worker；附加報告不得自稱正式核准。
- 以工作站即時盤點為準；先前紀錄的 46 境、BASE 317 件／136 條衝突，是歷史證據，不是目前數值。必須傳入固定 `--base-python`；不可把「誰執行腳本」當作穩定的 BASE 身分。

## 八路本機檢查 + uv

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
| +uv | 待安裝全集解析，不寫入現況 | `uv pip install --dry-run --python <該境解譯器>`；網路同意閘未開時附加 `--offline`，快取不足標 `NOT_RUN` |

診斷工具清單為 `pip`、`pipdeptree`、`deptry`、`pipgrip`、`johnnydep`、`pip-tools`、`pip-check-reqs`、`packaging`，由既有 Baseline 管理版本與安裝位置；不得為「湊足八路」直接灌入 BASE。後六種診斷工具提供相依圖、專案宣告及候選解析的加強證據，**不是每一種都能單獨證明環境無衝突**；未安裝時如實列為缺件，按工具冊路由。

## 分階決策

1. 預檢：固定 BASE 解譯器與 `C:\Users\tonyk\envs`，列出 BASE、所有 `via_*` 境的 Python、套件及工具現況；保留 RunGate、LKGC 的上一個逐境成功紀錄。
2. 分流：缺件與風險件取自同一份工具冊。一般件按既定家族放置；特殊語言工具與相依函式庫用對應獨立境；MEDIUM／HIGH 只能進各自 `_M`／`_H` 境。`numpy`、`pyarrow` 等可在不同 Python／不同境使用不同版本；**同一境多版遮蔽或 ABI 錯配要封鎖**。
3. BASE 有衝突、身分漂移或封鎖家族件：停止安裝。先由現有 `via-envgov plan` 算出 BASE 修復／拉出計畫；移除 BASE 套件必須經既有 `--approve-remove` 與目標境驗綠。
4. 在位境身分或 ABI 錯位：標 `REBUILD_REQUIRED`，導向 `via-rebuild --env <name>` 的現有重建流程。保留舊境與 LKGC，不能靠再補裝輪子掩蓋錯配；正式境替換由 CGC Promote Worker 治理。
5. 缺少的 `via_*` 境：先由 RunGate GREEN 或 MDL135 已驗證的 bootstrap 例外建立空境，再對**實際解譯器**執行八路檢查和 uv 解析。
6. 八路及 uv 檢查都通過、網路同意閘已開時，交既有 MDL135 `tools_apply` 安裝 GREEN 非破壞段；不執行卸載、`uv pip sync`、移除境或改 Active Pointer。
7. 安裝後再做完整盤點、`pip check`／uv 檢查與工具冊差量比對。只有所有必要項零缺件且零衝突才可記 PASS，並透過現有 LKGC 記錄逐境成功版本；失敗保留 before／after 和前次成功還原點。

## 存證及 Lesson Learned

每跑在 `VIA_Reports/env_governance/eight_hub/` 保存帶時間的 JSON、Append-Only 事件及 `OBSERVED_ONLY` 教訓候選：BASE 絕對路徑、各境 Python 版本、套件版本、工具缺件、八路結果、uv 解析、執行結果和複驗。連續故障以 `env + hub + state` 指紋去重；只有人工核准過的 Lesson Learned 才能升格預防規則。`BLOCKED`、`NOT_RUN`、`REVIEW` 不可當 PASS。

## 工作站入口

從既有母系統 PowerShell 入口載入環境後執行：

```powershell
$ViaEnvRoot = 'C:\Users\tonyk\envs'
$ViaBasePython = 'C:\Python313\python.exe' # 以目前 BASE 身分紀錄核定，勿用 PATH 自動換人
via-envgov eight-hub --env-root $ViaEnvRoot --base-python $ViaBasePython
via-envgov eight-hub --env-root $ViaEnvRoot --base-python $ViaBasePython --execute
```

第二行只在既有 `VIA_NET_CONSENT` 與 RunGate／bootstrap 閘已通過時執行 GREEN 非破壞段；本政策不代設同意閘。HTML Matrix／正式政策晉升仍由中央治理入口處理。

# 側線 2026-09-29 e:GitHub Actions 升到 Node 24 版 —— checkout · setup-node · setup-python · upload-artifact 一律 v7

主線批號由併線的手指定(L25)。本批接在 PR #370(d66fdaee)之後。

## 一、操作員令(原文)

- 「升級那四個 action,開 PR」

## 二、為什麼

PR #370 的 CI(run #970)綠,但帶 1 個 warning —— GitHub 平台的 Node.js 20 淘汰通知:
`actions/checkout@v4 · actions/setup-node@v4 · actions/setup-python@v5 · actions/upload-artifact@v4` 還是 Node 20 版,runner 已強制改用 Node 24 跑。
這個 workflow 每一輪都出現,與各批改動內容無關。

## 三、先量:每個大版本實際跑哪一版 Node

讀各 action 自己 tag 上的 `action.yml`(`runs.using`),不看版號猜:

| action | v4 | v5 | v6 | v7 |
|---|---|---|---|---|
| checkout | node20 | node24 | node24 | node24(v7.0.1) |
| setup-node | node20 | node24 | node24 | node24(v7.0.0) |
| setup-python | — | node20 | node24 | node24(v7.0.0) |
| upload-artifact | node20 | **node20** | node24 | node24(v7.0.1) |

upload-artifact 的 v5 仍是 node20 —— 只看「版號比較新」會升錯。

## 四、選 v7(四支都是目前最新大版本,都跑 node24),對照我們用到的輸入

| action | 我們用的輸入 | 舊版 → v7 的輸入差異(action.yml 實比) | 影響 |
|---|---|---|---|
| checkout | `sparse-checkout`(非 cone)· 預設 `persist-credentials`(狀態報告工作流靠它 `git push`) | 無增減、預設不變 | v6 起憑證改存 `$RUNNER_TEMP`,官方說明 `git fetch` / `git push` 照常;v7 只擋 `pull_request_target` / `workflow_run` 觸發的 fork PR checkout —— 我們用的是 `push` / `pull_request` / `workflow_dispatch` |
| setup-node | `node-version: "22"` | 移除 `always-auth`(沒用)· 加 `package-manager-cache` | v6 起自動快取只在 `package.json` 的 `packageManager` = npm 時開;倉根沒有 `package.json` → 不觸發。v7 只是內部改 ESM |
| setup-python | `python-version: "3.12"` | 加 `pip-version`(選用) | v7 官方說明:輸入 / 輸出 / 行為不變 |
| upload-artifact | `name` · `path` · `if-no-files-found` · `retention-days` | 加 `archive`(預設 `true` = 照舊壓 zip) | 無 |

## 五、改了哪裡(7 行)

- `.github/workflows/via-master-control-ui.yml`:checkout · setup-python · setup-node · upload-artifact ×2
- `.github/workflows/via-status-report.yml`:checkout · setup-python

不改的(照實):

- `VIA_HTML_UI` 套件裡的兩份 CI 範本(`ci/github-actions-via.yml` · `skills/via-ucc-triengine-workbench/templates/ci/github-actions-via.yml`,倉根與 `VeritasIntelligenceAnalytics/` 兩處):列在套件 `manifest.json`,CGC_MDL160 以 sha256 核套件完整性 —— 改了完整閘就紅;而且 GitHub 不跑這些檔。
- intake 正本(`VIA_QuantGuard_v20260916` 的 `ci.yml` · `VIA_CodexParallel_b305` 的 patch):正本零觸碰。

## 六、驗證

| 項 | 結果 |
|---|---|
| 兩份 workflow YAML 解析 | 通過;`.github` 底下舊版號 0 處;diff 只有這 7 行(換行不變) |
| 版本與輸入 | 四支 v7 的 `action.yml` 都是 node24;我們用到的輸入全在,沒有被移除或改預設的 |
| `via-master-control-ui.yml` 實跑 | 本 PR 的 CI 就是它(workflow 檔本身在觸發路徑裡),新版 action 由這一輪實跑;結果記在 PR |
| `via-status-report.yml` 實跑 | 只在 push 到 main(改到它列的檔)或手動觸發時跑;本 PR 合併就會觸發一次(workflow 檔本身在它的路徑裡)—— 合併後看那一輪的 checkout v7 + `git push` |

## 七、還原

- `git revert` 本批的合併提交;或把這 7 行改回 `checkout@v4` · `setup-node@v4` · `setup-python@v5` · `upload-artifact@v4`。

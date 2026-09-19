# VIA Playwright 跨裝置 E2E 與同步驗證指南

本文件說明如何在無頭 Chromium 中自動執行 VIA 中央管理 UI 的 Desktop、Tablet、Mobile E2E 測試，並說明 `VIA-SYNCHRONIZER-Standalone.html` 與中央 UI 之間的 `BroadcastChannel`、`localStorage` 與瀏覽器 `storage` event 同步流程。

## 1. 執行環境

VIA 正式入口是單檔 HTML，不需要 CDN、外部 chart runtime、資料庫或遠端 API。E2E runner 使用本機 Python Playwright 與已安裝的 Chromium；測試本身以 `file://` 載入中央 UI。離線環境應預先準備 Python 3、Chromium 與 Playwright，並以可攜方式把完整執行環境帶入隔離主機，不要在隔離主機執行 `pip install`。

```bash
python3 --version
chromium --version
python3 -m pip show playwright
```

如果目標瀏覽器對 `file://` 的 storage policy 不同，請使用只綁定 `127.0.0.1` 的 loopback fallback。這仍然不需要外部網路：

```bash
cd /opt/via/via_standardized_template_updated
python3 -m http.server 8765 --bind 127.0.0.1
```

接著使用 `http://127.0.0.1:8765/ui/...` 載入兩個 HTML。這個 loopback 只用於測試瀏覽器同源行為，不是產品部署依賴。

## 2. 三裝置 E2E runner

正式 runner 位於 `e2e/run_via_investment_e2e.py`。它用一個 Chromium browser 建立三個獨立 `BrowserContext`，每個 context 使用獨立 viewport，因此不會讓 Desktop 的 cookie、storage 或 DOM 狀態污染 Tablet 與 Mobile。

| Device ID | Width | Height | 目的 |
|---|---:|---:|---|
| `desktop-1440` | 1440 | 1000 | PC 橫向工作台、三欄卡片對齊 |
| `tablet-768` | 768 | 1024 | 平板轉折、側欄與面板壓縮 |
| `mobile-390` | 390 | 844 | 手機直向堆疊、搜尋展開與行動側欄 |

執行完整矩陣：

```bash
python3 e2e/run_via_investment_e2e.py \
  --html ui/VIA-UI-Standalone-NoServer.html \
  --devices desktop-1440,tablet-768,mobile-390 \
  --out-dir e2e/results-local \
  --executable-path /usr/bin/chromium
```

`--headed` 是唯一會關閉無頭模式的選項；CI 與離線自動化不應加上它：

```bash
python3 e2e/run_via_investment_e2e.py \
  --html ui/VIA-UI-Standalone-NoServer.html \
  --devices desktop-1440,tablet-768,mobile-390 \
  --out-dir e2e/results-headed \
  --headed
```

### Runner 的主要階段

第一，程式以 `sync_playwright()` 啟動 Chromium，使用 `headless=not args.headed`、`--no-sandbox` 與 `--disable-gpu`。第二，對每一個 device 呼叫 `browser.new_context(viewport=..., locale="zh-TW", reduced_motion="reduce")`，建立乾淨的 page。第三，使用 `html_path.as_uri()` 產生 `file://` URI，等待 `load` 與 `#investmentDesk` 可見後才開始斷言。

每個斷言都透過 `DeviceSuite.check()` 包裝。單項失敗會被記錄而不會立刻中止整個矩陣，使報告能同時呈現所有失敗點；只有頁面啟動或導覽發生 catastrophic failure 時才會加入 `suite_fatal_error`。

測試涵蓋以下功能群：

| 群組 | 斷言內容 |
|---|---|
| Standalone contract | 沒有外部 script、stylesheet、`fetch()`、WebSocket 或 EventSource |
| Responsive | document/body 沒有水平溢出；投資卡片在 PC 對齊、手機堆疊 |
| Chart engine | bars、area、line 模式；1D、1W、1M、3M；tooltip 與 crosshair |
| Investment UI | 市場範圍、watchlist、全域搜尋、設定抽屜、連線 modal |
| Extension | UI Lab、add-on registration、Engine Hub state snapshot |
| Flow | 導覽切換、暫停／恢復資料流、行動版側欄 |
| Quality | accessibility landmarks、console error、page error |

測試完成後會建立：

```text
e2e/results-local/report.json
 e2e/results-local/report.md
 e2e/results-local/junit.xml
 e2e/results-local/screens/desktop-1440.png
 e2e/results-local/screens/tablet-768.png
 e2e/results-local/screens/mobile-390.png
```

CI 應使用 `report.json` 判斷總結果，使用 `junit.xml` 對接測試平台，使用 PNG 與 `report.md` 做人工視覺回歸。

## 3. 同步狀態 envelope

兩個 HTML 共用以下名稱：

| 常數 | 值 | 用途 |
|---|---|---|
| `KEY` | `via.sync.state.v2` | localStorage 的 version 2 狀態 envelope |
| `LEGACY_KEY` | `via.sync.state.v1` | 舊版狀態遷移來源 |
| `CHANNEL` | `via.sync.v2` | BroadcastChannel 名稱 |

標準化 state 會包含 `version`、`updatedAt`、`source`、`view`、`modules`、`analytics`、`layout` 與 `sync`。其中：

- `view` 保存 density、theme、motion、hints、live、autoApply、paused、activeTab 與 activeNav。
- `modules` 保存 system/custom module、enabled、pinned、order 與 type。
- `analytics` 保存 templateId、templateName、charts、history 與 pivot。
- `layout` 保存 fontScale、headerHeight、panelHeight、equalPanels 與 surface。
- `sync` 保存 scope、conflict、debounceMs 與 revision。

初始化時兩邊都先從 `localStorage.getItem(KEY)` 讀取；如果沒有 v2，會嘗試讀取 `LEGACY_KEY`，再由 `normalize()` 轉成 version 2。若瀏覽器禁止 storage，程式會將 `canStore` 設為 false，UI 仍可執行，但必須使用 JSON 匯出／匯入取代跨頁持久化。

## 4. SYNCHRONIZER → 中央 UI 的同步流程

SYNCHRONIZER 內的 `persist()` 是來源端的主要寫入函式。它會先 normalize state，依需要增加 `sync.revision`，更新 `updatedAt` 與 `source='SYNCHRONIZER'`，再寫入 localStorage。當 `broadcast=true` 且 scope 不是 `manual` 時，會呼叫：

```javascript
bc.postMessage({
  type: 'via-state-v2',
  originId,
  state: clone(state)
});
```

中央 UI 的 `channel.onmessage` 收到 `via-state-v2` 後，會排除相同 `originId`，再呼叫 `apply(event.data.state, true)`。`apply()` 會 normalize incoming state，依同步 scope 套用 layout、view、modules 與 analytics，重新渲染自定義模組，最後以 `write(activeState, false)` 保存，但不再次廣播，避免 feedback loop。

中央 UI 的同步修正特別保留了兩個欄位：

```javascript
if (scope !== 'view-only') {
  activeState.modules = state.modules;
  activeState.analytics = state.analytics;
}
if (scope !== 'modules-only') {
  activeState.layout = state.layout;
}
```

這可避免 SYNCHRONIZER 套用投資研究模板後，中央 UI 只更新側欄模組卻遺失 `templateId`、history、chart 與 layout 的問題。

## 5. 中央 UI → SYNCHRONIZER 的同步流程

中央 UI 互動事件會在 click/change 後呼叫 `publish('UI')`。`current()` 會從目前 DOM 與 `activeState` 組出新的 version 2 state，再增加 revision 並呼叫 `write(activeState, true)`。因此，像 density、theme、motion、pause flow、active tab 或自定義模組導覽改變，都可同步回 SYNCHRONIZER。

SYNCHRONIZER 收到 `via-state-v2` 後會呼叫 `applyIncoming()`。它先 normalize，再依 `sync.conflict` 判斷是否接受：

| Conflict rule | 行為 |
|---|---|
| `latest` | 比較 `updatedAt`，接受較新的狀態 |
| `local` | 保留本頁狀態，不接受遠端覆蓋 |
| `remote` | 接受遠端狀態 |

接受後，SYNCHRONIZER 依 scope 執行 `applyScope()`，更新 controls、模組、圖表、歷史資料與 pivot，寫回 localStorage 並標記 `source='REMOTE'`，但不重新廣播。

## 6. localStorage fallback 與 storage event

`BroadcastChannel` 是即時通道，但不是唯一通道。兩頁都註冊：

```javascript
window.addEventListener('storage', event => {
  if (event.key === KEY && event.newValue) {
    // normalize and apply incoming state
  }
});
```

`storage` event 通常只會在「其他同源頁面」觸發，不會在執行 `localStorage.setItem()` 的同一頁觸發。因此它適合作為 BroadcastChannel 不可用或訊息遺失時的 fallback。這也是為什麼跨頁測試必須使用兩個 page，而不能只在同一個 page 裡反覆 setItem。

`clearState` 會移除 v2 與 legacy key，並以 `via-clear-v2` 廣播。收到清除事件的頁面會重新 normalize 空 state 並回到預設模組。若 scope 是 `manual`，一般 state broadcast 會被禁止，但 clear message 仍可讓其他頁面恢復預設。

## 7. 跨頁同步 Playwright 腳本

正式腳本位於 `e2e/test_via_cross_page_sync.py`。它在同一個 BrowserContext 建立兩個 page，因此保留相同的 file origin、localStorage 與 BroadcastChannel namespace：

```bash
python3 e2e/test_via_cross_page_sync.py \
  --ui ui/VIA-UI-Standalone-NoServer.html \
  --synchronizer ui/VIA-SYNCHRONIZER-Standalone.html \
  --out e2e/results-cross-page/report.json \
  --executable-path /usr/bin/chromium
```

腳本的 11 個檢查包含：

1. 兩個頁面共用同一個 file origin。
2. UI channel、storage key 與 SYNCHRONIZER capability checkbox 正確。
3. SYNCHRONIZER 套用 `investment-research` 後，中央 UI 收到模板與模組。
4. 中央 UI 收到 28 筆 history，並保留 10 個 system/custom modules。
5. 中央 UI 套用 compact density 後，SYNCHRONIZER 收到 view state。
6. 兩頁的 version 2 storage envelope 與 revision 一致。
7. 直接改寫 localStorage 後，SYNCHRONIZER 透過 `storage` event 收到 `highContrast`。
8. `view-only` scope 不會把 SYNCHRONIZER 新增的 module 傳入中央 UI。
9. `modules-only` scope 不會把 UI 的 theme/view 覆蓋回 SYNCHRONIZER，但仍可同步模組資料。
10. `manual` scope 允許本頁 CSS 視覺改變，但不會把新的 snapshot 廣播給另一頁。
11. 腳本將每項結果寫入 JSON，便於 CI 或人工診斷。

目前基準結果為 **11/11 PASS**。

## 8. 建議 CI gate

建議把兩個 runner 串成同一個 quality gate：

```bash
set -euo pipefail

python3 e2e/run_via_investment_e2e.py \
  --html ui/VIA-UI-Standalone-NoServer.html \
  --devices desktop-1440,tablet-768,mobile-390 \
  --out-dir e2e/results-ci \
  --executable-path /usr/bin/chromium

python3 e2e/test_via_cross_page_sync.py \
  --ui ui/VIA-UI-Standalone-NoServer.html \
  --synchronizer ui/VIA-SYNCHRONIZER-Standalone.html \
  --out e2e/results-ci/cross-page-sync.json \
  --executable-path /usr/bin/chromium

python3 skills/via-e2e-zip-verifier/scripts/validate_standardized_package.py \
  . --run-e2e --out-dir /tmp/via-ci-package
```

CI 應將任一 runner 的 non-zero exit code 視為失敗。Smoke test 完成後，請清除測試 profile 或 file-origin storage，避免上一次模板、density 或 theme 污染下一次測試。

## 9. 已驗證結果

本次修正版已實際驗證：三裝置 E2E **54/54 PASS**、Desktop／Tablet／Mobile 各 18/18、browser/page errors 為 0；標準化離線 smoke test **18/18 PASS**；ZIP 解壓後完整驗證 **21/21 PASS**；跨頁同步測試 **11/11 PASS**。

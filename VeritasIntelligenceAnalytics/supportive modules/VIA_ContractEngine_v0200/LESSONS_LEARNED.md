# VIA v0.2.0 · 測試整合 Lesson Learned

## def 01 已轉成永久規則的教訓

| ID | 測試整合發現 | 根因 | v0.2.0 修正 | 永久回歸規則 |
| --- | --- | --- | --- | --- |
| LL-01 | `novalidate="false"` 仍會關閉瀏覽器驗證 | HTML Boolean Attribute 只看「是否存在」 | 完全移除該屬性 | HTML 測試必須斷言不存在 `novalidate` |
| LL-02 | 字串 `"五百"` 若進入模組才失敗，會污染資源 | 驗證太晚且 DI 已建立 | Pydantic Input 在 DI 前驗證 | 非法 Input 時 Provider open/close 必須皆為 0 |
| LL-03 | 只靠檔名註冊會因 rename／copy 產生身份漂移 | Filename 不是穩定 Identity | 使用 Manifest + Version + SHA-256 配發不可變 URN | 同一 Source Identity 重跑必須取得同一 URN |
| LL-04 | Watchdog 直接 import 新檔等同執行未審程式 | Python import 有任意 Side Effect | AST／JSON 靜態解析，僅 Stage 為 `DISCOVERED` | Watchdog 測試不得觸發候選模組程式碼 |
| LL-05 | Registry dict 無鎖會出現讀寫競態 | 多執行緒同時註冊／健康檢查 | Writer-Preferring RW Lock | 並行 writer 測試與 snapshot 一致性測試常駐 |
| LL-06 | 只依模組名稱 setup 會違反依賴順序 | 缺少 DAG 與 Cycle Gate | `register_many()` 先 Topological Sort | 子模組先輸入也必須先 setup 父模組；Cycle 必須拒絕 |
| LL-07 | 任意卸載父模組會讓子模組成為懸空實例 | 缺少 reverse dependency guard | 有 dependent 時拒絕；shutdown 逆拓撲 | Parent unload 必須在 Child 存在時失敗 |
| LL-08 | `setup()` 成功不代表模組可服務 | 初始化成功與健康狀態混為一談 | 首次 `health_check()` 通過才進 `READY` | False／Exception 必須 Fail-Closed 到 Error/Unhealthy |
| LL-09 | 只記錄 PASS/FAIL 無法診斷執行品質 | 缺少 per-module operational evidence | Success／Failure／Timeout／Validation／Health metrics | 執行、拒絕、健康檢查均須增加正確 counter |
| LL-10 | Output dict 看似可用但可能違反合約 | 只驗 Input，未驗 Output | 回傳值再經 Pydantic Output Contract | 錯誤 Output 必須拒絕並將模組標為 Error |
| LL-11 | UI 以 CSS class 定位容易因設計調整破裂 | Test selector 與視覺樣式耦合 | 使用 `data-via-command/field/action/urn` | UI Twin 只能依語意 selector 與 Schema constraint 驗證 |
| LL-12 | SQLite 有紀錄不等於共享 Python instance | Durable identity 與 runtime memory 混淆 | 明確區分 Ledger 與 Process Singleton | 文件與 Snapshot 必須同時顯示 PID／instance locator |
| LL-13 | Proposal／Discovered 容易被誤報為 Activated | 生命週期狀態語意不嚴格 | `DISCOVERED → SETTING_UP → READY` 分離 | `DISCOVERED` 必須 `instance=None` 且不可 execute |
| LL-14 | Thread timeout 無法安全中止同步 Python 邏輯 | CPython Thread 缺少強制安全終止 | 本版不虛構同步硬中斷能力 | 高風險外掛進 Process Sandbox 後才能聲稱可強制 timeout |

## def 02 對後續整合的決策

1. Loader 必須是獨立 Gate：`Static PASS` 不自動等於 `Import Allowed`。
2. 跨 Process 共享狀態使用 durable event／database；Python object 只存在建立它的 Process。
3. 生產 Promote 前加入簽章／Allowlist、權限 Manifest、Process Sandbox 與 Rollback Drill。
4. 每個新子系統註冊時必須同時交付 Manifest、Input/Output Contract、Health Check、Dependency Test、Teardown Test 與 UI Twin Test。
5. 每輪測試證據要區分 Static、Unit、Integration、System、User Test 與 Activation，不再把其中一層 PASS 外推成整體已啟用。

# VIA 標準化模板 QA 驗證基準

本標準化模板的基準驗證包含 canonical launcher、19 項結構、offline guide、registry、standalone contract、inline JavaScript、E2E、JUnit 與 legacy boundary 檢查。完整套件 pipeline 另執行跨頁同步與 optional companion smoke test。最新來源基準為 19/19 PASS。

跨裝置 E2E 使用三個 viewport：桌機 1440×1000、平板 768×1024、手機 390×844。基準報告共有 54 項檢查，結果為 54/54 PASS，三個裝置均無 browser/page error，也無水平 overflow。

解壓後的標準化模板必須再次執行 `skills/via-e2e-zip-verifier/scripts/validate_standardized_package.py --run-e2e`。ZIP 發布版則另外執行 `skills/via-e2e-zip-verifier/scripts/validate_standardized_zip.py --run-extracted-e2e`，並在 ZIP 外部保存 checksum 與 release verification JSON，避免自我 hash 循環。

離線 acceptance criteria 另外要求：完整 launcher、兩個正式入口可由 `file://` 開啟；SYNCHRONIZER 同源頁籤可驗證 version 2 state、`localStorage` 與 `BroadcastChannel`；必要時可用 `127.0.0.1` loopback 作為不連外的瀏覽器 fallback；測試不得依賴下載 CDN 或遠端 API。

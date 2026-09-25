========================================================================
 VIA Active ETF — 最終版部署包 (FINAL, tested)
 Visual Lock v1 · 單檔多頁 UI · PARQUET 增量 · PWA · 每日更新
 產生日期：2026-06-02
========================================================================

【資料夾結構】
  vetf\                         → 整夾複製到
                                   C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\vetf\
  supportive_sort\              → 整理 supportive_module 用（USED 複製到 Desktop modules、其他移到 others）
  RUN_VIA_Deploy.ps1            → 自尋並執行部署（找不到/誤存.txt 時用）

------------------------------------------------------------------------
【vetf\ 內容】
  VIA_ActiveETF_System.py        ONE PY：抓取→PARQUET 增量→eco 守門→注入建單一多頁 HTML
  VIA_ActiveETF.ps1              啟動器：選 BASE/DICT→sync(非阻塞)→跳出 Console UI
  VIA_ActiveETF_Pack.ps1         打包器：整合→複製 dist→編譯自帶 UI 的 EXE + PWA 資產
  VIA_DeployAll.ps1              ★ 結案部署（推薦）：稽核→自動補裝 pyarrow/pandas/yfinance→
                                  基準快照→PATH→首次 sync→每日排程；原子化貼上、不關閉視窗、非阻塞
  console_merged_template.html   單一模板（PY 注入 __PERF__/__HOLD__/__LOGO__/__BASE__/__DICT__）
  VIA_ActiveETF_Console.html     已建好的單一多頁 UI（績效 Matrix + 持股 Flow，內嵌資料+logo，PWA+響應式）
  VIA_logo.png                   去背銀色徽章
  VIA_ActiveETF.webmanifest      PWA manifest
  sw.js                          PWA service worker（離線快取）
  icon-192.png / icon-512.png    PWA 圖示
  VIA_ActiveETF_PackList.json    打包/整合/部署全紀錄

------------------------------------------------------------------------
【一鍵流程】
  1) 把 vetf\ 整夾複製到 ...\modules\vetf\
  2) 在你開著的 PS7 執行（視窗不會關）：
       & "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\vetf\VIA_DeployAll.ps1"
     → 自動補裝缺套件、eco PASS、首次 sync、排程每日 08:00 更新
  3) 開 UI：雙擊 vetf\VIA_ActiveETF_Console.html（或 & ...\VIA_ActiveETF.ps1）
  4) 打包 EXE/PWA（可選）：
       & "...\vetf\VIA_ActiveETF_Pack.ps1"            → dist\VIA_ActiveETF.exe + PWA
       & "...\vetf\VIA_ActiveETF_Pack.ps1" -SyncBundle → EXE 內含可重抓資料

------------------------------------------------------------------------
【整理 supportive_module（可選）】
  & "...\supportive_sort\VIA_SupportiveModule_Sorter.ps1"            → 預覽計畫(CSV)
  & "...\supportive_sort\VIA_SupportiveModule_Sorter.ps1" -Execute  → USED 複製到 Desktop modules、其他移到 others
  USED 4 支：VeritasAegisNexus.py / VeritasCeleritas.py / VIA_EnvManager.py / VIA_SSOT_Unified.py

------------------------------------------------------------------------
【環境（已驗）】Python 3.11/3.12 · numpy>=1.24,<2.0 · pyarrow · pandas · (yfinance 接真實量價時)
【LL】param 頂部 · 全名函式 · py 啟動器 · [IO.File] · .Replace · 無 Start-Job · 非阻塞 ProcessStartInfo
【測試】PY selftest 4/4 · 5 支 PS 括號平衡無 Start-Job · Console 雙頁 25/11 列 0 錯誤 · PWA/響應式驗證

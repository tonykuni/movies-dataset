# VRN-2 v0157 驗證紀錄(2026-10-31 · ③ 預設不 pip · 缺的經 VCGC 安裝閘 · 套件 v0157 · RoundAll v0113 · Handle-All v0105)

## 1. 要求與桌機狀態

操作員 2026-10-31:「預設關掉 ③ 的 pip 補裝，改經 VCGC 安裝」。同時貼回桌機 04:13 Handle-All v0104 repair:③b `VIA_NET_CONSENT=YES · VIA_SCRAPE_CONSENT=(未設)`
→ 閘二沒開 → ⑥f 不重抓 → **BLOCKED · VRN-2 0 · VCGC 1 · 人工 3 · 資料源 2**(跟 v0156 預期的「閘關」一樣)。

## 2. 根因(容器裡看到的)

管理器 `envcheck --install`(VRN_SystemManager v0231 起)用**這個 Python 直接 pip**,而且加 `-c constraints.txt`(`numpy>=1.24,<2.0`)。
v0156 沙盒整輪時它補裝了幾個套件,numpy 被降到 1.26.4、pyarrow 讀不起來。

## 3. 做了什麼

| 檔 | 版本 | SHA-256 | 說明 |
|---|---|---|---|
| 啟動器 | v0157 | `850c0d07d38d` | 攔下底座 ③ 的 envcheck:拿掉 `--install`(只檢查)→ 缺的一個一個交 VCGC `CGC_MDL056_InstallGate` 最高版號 → 裝完再檢查 · 24 小時不重試 · `--no-install` / `--plan` 不呼叫 · 找不到閘交 VCGC · 舊行為只有 `--pip-install` / `VIA_VRN2_PIP_INSTALL=1` |
| RoundAll | v0113 | `891df58a576e` | ② 提示改經 VCGC 安裝閘 · 除錯報告「③ 環境檢查 · VCGC 安裝閘沒裝起來」(必裝黃 / 選裝灰)· 貼回包帶安裝帳 |
| Handle-All | v0105 | 一行 `c3a93278037a` | 指向 RoundAll v0113 |
| 套件 | VRN2_Closeout_v0157.zip | `7ff4e9626abf` | runtime v0156 原樣(同一個 zip) |

③b OCR 隔離環境沒改:它在自己的 venv 裡 pip(不是主 Python);VCGC 安裝閘只裝進呼叫它的那個 Python。

## 4. 自測

```text
[PASS] 56 ③ 經 VCGC 安裝閘:除錯報告列 VCGC 安裝閘沒裝起來的必裝(黃 · via-install · 收尾頁 VCGC)· 選裝灰 · ② 不再印 pip 指令 · 貼回包帶安裝帳
[PASS] 57 收尾頁:② 磁碟可用不到 2 GB → 人工(清空間 · 不是 VRN-2 要改碼;沙盒整輪 v0157 實錄被算成 VRN-2 2 項)
[PASS] VRN2_RoundAll v0113 --selftest · 57 項 · 不過 0
[PASS] v0157: step 3 runs envcheck check-only (no pip in this Python) · missing packages go one by one through VCGC's newest CGC_MDL056_InstallGate · re-checked after an install · gate failures not retried for 24 h · --n
[PASS] v0156: ConsensusJoin v0104 is the active consensus join · engine v0122 (highest in the runtime) goes out through the VIA network tool SUP_MDL740_NetUnified + accelerator bridge · gate closed → net_deny, never anot
pwsh 7.4.6 剖析 0 錯 · Handle-All 一行 = 可讀版 · 開機行 = 可讀版 · 最短一行 0 錯
e2e 結束碼:report rc 0 · auto rc 0 · full rc 0 · tamper rc 0 · venv unchanged
```

## 5. ③ 經 VCGC 安裝閘

沙盒整輪(VCGC 安裝閘 v0104 放進沙盒 VIA · 同意閘不設):沙盒的 Python 不缺套件 → ③ 只檢查就綠,沒呼叫安裝閘。

```text
[計] ④ 模式 full:整輪(取套件 v0157 → 診斷 → 全部自測 → 跑啟動器 v0157(③ 只檢查 · 缺的經 VCGC 安裝閘 · 管理器 v0257 · ⑥f ConsensusJoin v0104 · 共識引擎 v0122 經 VIA 網路工具 + 加速器)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 40 分鐘)
       → 啟動器 v0157 ③ 只檢查 · 缺的經 VCGC 安裝閘(CGC_MDL056_InstallGate)裝 · 仍缺 → 交 VCGC:via-install pyarrow(VRN-2 不 pip)
         "%USERPROFILE%\envs\via_tw_fetch\Scripts\python.exe" -m pip install "pandas>=2.2,<3" "pyarrow>=17,<27" "duckdb>=1.1,<3" "yfinance>=0.2.54,<2" "lxml>=5,<7" "tzdata>=2024.1"
         cmd        : "%USERPROFILE%\envs\via_tw_fetch\Scripts\python.exe" -m pip install "pandas>=2.2,<3" "pyarrow>=17,<27" "duckdb>=1.1,<3" "yfinance>=0.2.54,<2" "lxml>=5,<7" "tzdata>=2024.1"
         PowerShell : & "$env:USERPROFILE\envs\via_tw_fetch\Scripts\python.exe" -m pip install "pandas>=2.2,<3" "pyarrow>=17,<27" "duckdb>=1.1,<3" "yfinance>=0.2.54,<2" "lxml>=5,<7" "tzdata>=2024.1"
  [███░░░░░░░░░░░░░░░░░]  18% · ③ 環境檢查與補裝(序跑:補裝會動到套件 · 先做完別的步驟才匯入)
  [計] 環境檢查(只檢查 · 不 pip · 缺的經 VCGC 安裝閘)· 沒有缺的 · 缺:必裝 0 · 選裝 0
    → GREEN ③ 環境檢查與補裝 · [計] 環境檢查(只檢查 · 不 pip · 缺的經 VCGC 安裝閘)· 沒有缺的 · 缺:必裝 0 · 選裝 0 · 耗時 3 秒
  [計] ③ 環境檢查與補裝 · [計] 環境檢查(只檢查 · 不 pip · 缺的經 VCGC 安裝閘)· 沒有缺的 · 缺:必裝 0 · 選裝 0 · 耗時 3 秒
       → 交 VCGC 建 via_tw_fetch(帶界線):PowerShell : python -m venv "$env:USERPROFILE\envs\via_tw_fetch" ; PowerShell : & "$env:USERPROFILE\envs\via_tw_fetch\Scripts\python.exe" -m pip install "pandas>=2.2,<3" "pyarrow>=17,<27" "duckdb>=1.1,<3"
```

整合測(`integ157.py`:v0157 的 `env_step` + **真的** VCGC 安裝閘 v0104 · envcheck 輸出用假的「缺 必裝 1 個」· 同意閘不設):

```text
[計] 環境檢查(只檢查 · 不 pip)· VCGC 安裝閘 CGC_MDL056_InstallGate_v0104 · 裝好 0 · 沒裝 1 vrn2-probe-not-a-real-package · 略過 0
[計] 補裝失敗 必裝 vrn2-probe-not-a-real-package · VCGC 安裝閘 CGC_MDL056_InstallGate_v0104 rc 1 · 同意閘未開——安裝需 $env:VIA_NET_CONSENT='YES'(紅線:不代設) → 交 VCGC:via-install vrn2-probe-not-a-real-package
[計] 環境檢查(只檢查 · 不 pip)· VCGC 安裝閘 CGC_MDL056_InstallGate_v0104 · 裝好 0 · 沒裝 1 vrn2-probe-not-a-real-package · 略過 0
[計] 補裝失敗 必裝 vrn2-probe-not-a-real-package · VCGC 安裝閘 CGC_MDL056_InstallGate_v0104 rc 1 · 同意閘未開——安裝需 $env:VIA_NET_CONSENT='YES'(紅線:不代設) → 交 VCGC:via-install vrn2-probe-not-a-real-package
[PASS] v0157 ③ 整合:真的 VCGC 安裝閘 v0104 被呼叫 · 同意閘不設 → 誠實 FAIL · 帳記必裝 · 交 VCGC via-install · envcheck 沒帶 --install
```

## 6. 最短一行 e2e(沙盒 = 桌機 v0153 狀態 · pwsh 7.4.6)

```text
[report] [GREEN] boot: Handle-All v0105 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[report] [YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=(未設) · VIA_SCRAPE_CONSENT=(未設))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」
[report] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝
[report]   [VCGC] 5 項
[report]   [人工] 2 項
[report] [計] Handle-All 結束 · RoundAll 結束碼 1 · 0 秒(視窗不會關)
[auto] [GREEN] boot: Handle-All v0105 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[auto] [YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=(未設) · VIA_SCRAPE_CONSENT=(未設))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」
[auto] [計] ④ 自動選模式 repair · 上一輪收據 VRN2_Closeout_v0153.json · 上一輪輸出冊 有(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識出網 → 不整輪)(整輪:先貼 $env:VRN2_MODE = 'full')
[auto] [計] ⑤ 自動修計畫:市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據)
[auto] ===== 收尾 · OPEN · 未結案 · VRN-2 還有 3 項要修
[auto]   [VRN-2] 3 項
[auto]   [VCGC] 3 項
[auto]   [人工] 2 項
[auto] [計] Handle-All 結束 · RoundAll 結束碼 1 · 3 秒(視窗不會關)
[full] [GREEN] boot: Handle-All v0105 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[full] [YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=(未設) · VIA_SCRAPE_CONSENT=(未設))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」
[full] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 6 項等 VCGC 決定 / 安裝
[full]   [VCGC] 6 項
[full]   [人工] 1 項
[full] [計] Handle-All 結束 · RoundAll 結束碼 2 · 1165 秒(視窗不會關)
[tamper] [RED] boot SHA-256 mismatch - not run
```

## 7. 桌機預期

貼 `VRN2_HandleAll_v0105.md` 最上面那行 → auto → repair(不跑啟動器 · ③ 這輪不跑)→ 閘照舊 = BLOCKED · VRN-2 0 · VCGC 1 · 人工 3 · 資料源 2;
兩道閘都設 → 人工 2。整輪才跑 ③:缺的經 VCGC 安裝閘(桌機有 `VIA_NET_CONSENT=YES`,安裝閘的 SuperAccel 安裝道會放行)。

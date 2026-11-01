# VRN-2 v0158 驗證紀錄(2026-10-31 · ③b OCR 隔離環境也不 pip · 套件 v0158 · RoundAll v0114 · Handle-All v0106)

## 1. 要求與桌機狀態

操作員 2026-10-31:「依照你的建議進行」(v0157 回覆:③b OCR 隔離環境還在自己的 venv 裡 pip · 要不要也預設關掉)。
桌機 04:55 Handle-All v0105 repair:③b 同意閘 `VIA_SCRAPE_CONSENT` 未設 → **BLOCKED · VRN-2 0 · VCGC 1 · 人工 3 · 資料源 2**(跟預期一樣)。

## 2. 做了什麼

| 檔 | 版本 | SHA-256 | 說明 |
|---|---|---|---|
| 啟動器 | v0158 | `5850196fc0cb` | ③b:就緒 / 有指定的 OCR 環境照用;沒就緒 → 不建 venv、不 pip · 黃燈附建法交 VCGC · OCR 照舊排佇列 · 舊行為只有 `--pip-install` / `VIA_VRN2_PIP_INSTALL=1` |
| RoundAll | v0114 | `425397f5d724` | 收尾頁 ③b 沒就緒 → VCGC(以前落到預設 VRN-2)· 自測 58 項 |
| Handle-All | v0106 | 一行 `99598c668e4b` | 指向 RoundAll v0114 |
| 套件 | VRN2_Closeout_v0158.zip | `dfca4f6b13fb` | runtime v0156 原樣 |

VCGC 安裝閘只裝進呼叫它的 Python(`pip --user`),裝不進另一個 venv,所以 ③b 的隔離環境照 via_tw_fetch 的方式交 VCGC 建(VRN-2 只印建法)。

## 3. 自測

```text
[PASS] 57 收尾頁:② 磁碟可用不到 2 GB → 人工(清空間 · 不是 VRN-2 要改碼;沙盒整輪 v0157 實錄被算成 VRN-2 2 項)
[PASS] 58 收尾頁:③b OCR 隔離環境沒就緒(啟動器 v0158 不建不 pip)→ VCGC(以前落到預設 VRN-2)
[PASS] VRN2_RoundAll v0114 --selftest · 58 項 · 不過 0
[PASS] v0158: step 3b uses a ready / assigned OCR environment as before · not ready → no venv, no pip from VRN-2 · YELLOW with the build commands for VCGC · OCR stays queued · old behaviour only with --pip-install / VIA_
[PASS] v0157: step 3 runs envcheck check-only (no pip in this Python) · missing packages go one by one through VCGC's newest CGC_MDL056_InstallGate · re-checked after an install · gate failures not retried for 24 h · --n
pwsh 7.4.6 剖析 0 錯 · Handle-All 一行 = 可讀版 · 開機行 = 可讀版 · 最短一行 0 錯
e2e 結束碼 / 環境檢查:report rc 0 · auto rc 0 · full rc 0 · tamper rc 0 · venv unchanged · ocr venv not created
```

## 4. 沙盒整輪的 ③ / ③b(沙盒沒有 envs/vrn2_ocr)

```text
    → GREEN ③ 環境檢查與補裝 · [計] 環境檢查(只檢查 · 不 pip · 缺的經 VCGC 安裝閘)· 沒有缺的 · 缺:必裝 0 · 選裝 0 · 耗時 3 秒
    → YELLOW ③b OCR 隔離環境 · OCR 隔離環境沒就緒(<v158>/t158a/home/envs/vrn2_ocr)· VRN-2 不建、不 pip(VCGC 安裝閘只裝進呼叫它的 Python · 裝不進別的 venv)→ 交 VCGC 建:python3 -m venv "<v158>/t158a/home/envs/vrn2_ocr" ; "<scratch>
  [計] ③b OCR 隔離環境 · OCR 隔離環境沒就緒(<v158>/t158a/home/envs/vrn2_ocr)· VRN-2 不建、不 pip(VCGC 安裝閘只裝進呼叫它的 Python · 裝不進別的 venv)→ 交 VCGC 建:python3 -m venv "<v158>/t158a/home/envs/vrn2_ocr" ; "<scratch>
[YELLOW] ⑥ 步驟 ③b OCR 隔離環境 · OCR 隔離環境沒就緒(<v158>/t158a/home/envs/vrn2_ocr)· VRN-2 不建、不 pip(VCGC 安裝閘只裝進呼叫它的 Python · 裝不進別的 venv)→ 交 VCGC 建:python3 -m venv "<scratch>
    · ⑥ 步驟 ③b OCR 隔離環境 · OCR 隔離環境沒就緒(<v158>/t158a/home/envs/vrn2_ocr)· VRN-2 不建、不 pip(VCGC 安裝閘只裝進呼叫它的 Py
```

## 5. 最短一行 e2e(沙盒 = 桌機 v0153 狀態 · pwsh 7.4.6)

```text
[report] [GREEN] boot: Handle-All v0106 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[report] [YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=(未設) · VIA_SCRAPE_CONSENT=(未設))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」
[report] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝
[report]   [VCGC] 5 項
[report]   [人工] 2 項
[report] [計] Handle-All 結束 · RoundAll 結束碼 1 · 0 秒(視窗不會關)
[auto] [GREEN] boot: Handle-All v0106 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[auto] [YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=(未設) · VIA_SCRAPE_CONSENT=(未設))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」
[auto] [計] ④ 自動選模式 repair · 上一輪收據 VRN2_Closeout_v0153.json · 上一輪輸出冊 有(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識出網 → 不整輪)(整輪:先貼 $env:VRN2_MODE = 'full')
[auto] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 3 項等 VCGC 決定 / 安裝
[auto]   [VCGC] 3 項
[auto]   [人工] 2 項
[auto] [計] Handle-All 結束 · RoundAll 結束碼 1 · 3 秒(視窗不會關)
[full] [GREEN] boot: Handle-All v0106 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[full] [YELLOW] ③b VIA 網路工具同意閘 未開(VIA_NET_CONSENT=(未設) · VIA_SCRAPE_CONSENT=(未設))· repair 不重抓 ⑥f(現有共識不動)· 整輪的 ⑥f 會被 DENY · 收尾頁列「人工」
[full] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝
[full]   [VCGC] 7 項
[full]   [人工] 1 項
[full] [計] Handle-All 結束 · RoundAll 結束碼 2 · 124 秒(視窗不會關)
[tamper] [RED] boot SHA-256 mismatch - not run
```

## 6. 桌機預期

貼 `VRN2_HandleAll_v0106.md` 最上面那行 → auto → repair(③ / ③b 不跑)→ 閘照舊 = BLOCKED · VRN-2 0 · VCGC 1 · 人工 3 · 資料源 2;先設 `VIA_SCRAPE_CONSENT` → 人工 2。
整輪才跑 ③b:桌機的 OCR 隔離環境以前建好了 → 照用;不在了 → 黃 · 收尾頁 VCGC 一項(建法在那一列)。

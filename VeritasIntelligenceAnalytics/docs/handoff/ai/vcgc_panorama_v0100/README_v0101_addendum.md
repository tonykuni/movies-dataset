# v0101 增補(2026-11-07 · Codex PR #603 P1 / P2;v0100 一字不改 · SHA256SUMS 仍指 v0100 原交付件)

- **P1 預設沿用收據**:`VCGC_Panorama_v0101.py` 第 11 步預設叫 `test`(主控台 CGC_MDL224 依相依判沿用、只重跑相依變了的站);要全站重跑用 `--force-full`(= `test --full`)。`--reuse-receipts` 保留為相容旗標。PS1 對應 `Invoke-VCGC-Panorama-v0101.ps1 -ForceFull`。
- **P2 逾時終止升級到整個 process group**:SIGTERM 群 → 等 10 s → SIGKILL 群(不論父行程是否已離開)→ 再 kill 父;Windows 照舊 `taskkill /T /F`。
- 測試:`test_vcgc_panorama_v0101.py` = v0100 的 13 項 + 預設 `test` / `--force-full` 兩段 + 「忽略 SIGTERM 的孫行程在逾時後被殺」;容器 14/14(`DELIVERY_QA_v0101.json`)。
- 桌機改貼:`pwsh -NoLogo -NoProfile -NoExit -File (Join-Path $ViaPack 'Invoke-VCGC-Panorama-v0101.ps1')`(其餘同 README 第一段)。

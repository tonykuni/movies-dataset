# VIA 每日收工檢核表 v0100(2026-11-17)

> 參考 ChatGPT「VCGC Daily Closeout Checklist」改成 VIA 版:每一勾都對到一個既有動詞或收據;不另建工具。
> 搭配:`VIA_FailureModes_FM20_v0100.json`(失敗模式與拒絕案例)· `VIA_RC1_LessonRegistry_v0102`(教訓)· 綠燈判準 G1–G8(專案文件「優化計畫」§三)。

日期:____ · 動作主力:Claude / ChatGPT · main HEAD:____ · 今日 PR:____

## A 省 Token 先開(FM-06)
- [ ] `via-vcgc token` → 已啟用 6/6(read · slice · digest · pack · etag · brief)
- [ ] 讀檔一律先 `read`(骨架卡)→ `slice`(一個定義);日誌用 `digest`;同檔再讀帶 `--if-etag`

## B GitHub(FM-07 · FM-16)
- [ ] 今日新增 / 併入 / 開著的 PR,交接檔各有一行
- [ ] 取版號 / 號碼前已掃 main ∪ 所有開著的 PR 分支(LESSON-0007)
- [ ] 同功能兩個 PR = 重工,今日 0 件(沒有自動偵測,逐 PR 看)
- [ ] 交付件只在交付分支,沒開 PR(LESSON-0008)

## C 交接(FM-08 · FM-11 · FM-18)
- [ ] `handoff check` 看完;pending 沒有消失,只有帶理由轉態
- [ ] `handoff checkpoint` 寫了
- [ ] `CGC_MDL283 run --actor <主力>`;先讀 `FEEDBACK_DELTA_latest.txt`

## D 綠燈有效(G1–G8)
- [ ] 今日新綠都有收據、夠新、範圍對帳、燈範圍講清楚
- [ ] 系統級綠有 Windows 主機收據;容器結果最多黃
- [ ] 成功鎖:退步 0,或每項有理由

## E 編號與註冊(FM-02 · FM-19)
- [ ] 新檔都有號;編號稽核 遺失 0 · 改身分 0 · 重號 0
- [ ] 沒有 AI 自行編號、沒有 AI 改律

## F 教訓(FM-03 · FM-09)
- [ ] 今日每個「重做」或「紅轉綠」記一條 LESSON(根因 · 影響 · 解法 · 預防 · 證據)
- [ ] 教訓冊出新版時同步存 Parquet

## G 備份(FM-15)
- [ ] `VIA_DailyBackup v0101 backup`;隔天 `check`(0 檔亮紅,不會假綠)
- [ ] git:今日分支都已推上 GitHub

## H 工具鎖與環境
- [ ] 鎖冊版 = 實際載入版(現況矩陣 C22)
- [ ] 外部工具收據 `tools/external` 沒有紅

## I 明天
- [ ] NEXT:一行寫明明天第一件事

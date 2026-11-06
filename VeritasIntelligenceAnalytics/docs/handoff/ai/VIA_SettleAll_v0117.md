# VIA_SettleAll v0117(2026-11-06 · ③ 同步:未追蹤衝突檔備份後重試合併 · v0116 一字不動)

## 為什麼

桌機 2026-11-06 23:45 貼回(SettleAll v0112 跑的):③ 同步 RED —— 工作樹在 `main` HEAD 122bab5f8,落後分支 262 提交、多 2 個沒推、改動 10、未追蹤 404;`git merge origin/claude/optimistic-goodall-yhalc5` 被 14 支**未追蹤檔**擋下(`would be overwritten by merge`:`docs/handoff/ai/VRN2_Handover_v0144.md` · `vrn2_release_v0144/*` · `vrn1_vrn2_oneclick_v0105/*` · `functional modules/VRN/VRN2_ChainShip_v0101.py` …,都是分支上也有的舊發布文件)→ `merge --abort`,④ VDF ui · ⑥ VCGC · ⑬ VDF 引擎全部「不在舊版上跑」。22:19 / 23:09 兩包同因。

## 差異(對 v0116)

| 項 | v0116 | v0117 |
|---|---|---|
| ③ 合併被未追蹤檔擋下 | abort → RED 回報 | 解析 git 點名的清單 → 逐支確認真的是未追蹤(已追蹤的一律不動)→ 移到 `VIA_Reports/settle/untracked_parked/<時戳>/<原相對路徑>`(原件保留 · sha 記在報告 `sync_parked`)→ **重試一次合併**;還是不成功才照舊 abort 回報 |
| 自測 | 45 項 | 47 項(+㊟ 錯誤文字解析 · +㊠ 沙盒 git 倉:未追蹤移走 · 已追蹤不動 · 不存在照實錯) |
| 其餘 | — | 一字不動(不 rebase · 不強推 · 不 push · 改動分類 / stash 放回 / 凍結版還原 · ⑧b · ⑰ · ⑯ · 矩陣) |

## 桌機

交接 `VRN2_Handover_latest.md` §32 一行(SHA `C0D6724B…`)。跑完若 ③ 綠,④ ⑥ ⑬ 就會在新尾版上跑;`untracked_parked/` 裡的原件要不要收回由操作員決定(都是分支上已有的舊發布文件)。

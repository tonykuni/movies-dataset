# 併 main 撞號退役(2026-11-16)

本線 `claude/gifted-dijkstra-e14m2m` 併 `origin/main` 時,下列檔與 main **同檔名不同內容**。依決定「main 已合併的檔保留原號」,
main 版留在原路徑;本線版原文(一字不改)搬到這裡,不在版號線上(檔名閘 N2 · 薄尾 glob 都不看退役夾)。

| 本線原檔 | 處置 | 理由 |
|---|---|---|
| VDF_ENG053_ParamEngineMap_v0103.py | 退役 | main v0103 修同一件事(車道 → 引擎源碼實證沿薄尾鏈);main 版自測 5/5 PASS |
| VDF_ENG236_FetchMatrixUI_v0102.py | 退役 | main v0102 修同一件事(自測不受本機資料家影響);main 版自測 4/4 PASS |
| CGC_MDL245_SDDValidator_v0108.py | 退役 | main v0108 修同一件事(樹外正主 rel() 不炸) |
| VDF_SystemManager_v0175.py | 退役 → 功能改出 v0184 | main v0175 以本線 v0174 全文為底;本線 v0175 的 collect 七項上游 + token 動詞改疊在 main v0183 上出 v0184 |
| VDF_SystemManager_v0172 / v0173 / v0174 | 退役 | main 線跳過 172–174 號(main v0175 的說明寫明以本線 v0174 全文為底);留在版號線上會讓 main v0183 自測 R2「前版每支都是標準轉交者」紅 |
| VDF_SSOTSync_v0101.py | 退役(待移植) | 同義字收割看穿薄尾。疊在 main v0102 上會讓 main v0102 自測 ④ 與本檔 ⑤ 互相打架(兩支都換 harvest);改由 VDF 自己出下一版整併,登在交接工作項 |

其餘撞號 / 夾在 main 版號線下的本線檔改發新版號(檔尾帶 `# [VIA:REISSUE]` 說明):
CGC_MDL237 v0120–v0122 → v0122–v0124 · CGC_MDL279 v0103–v0105 → v0104–v0106 · VRN_SystemManager v0263–v0267 → v0276–v0280 ·
VRN2_PeerBridge v0102–v0103 → v0103–v0104 · VRN2_ReportRows v0102 → v0103。

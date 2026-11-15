# VCGC 資訊卡:四系統能否各自獨立跑完(2026-11-14)

操作員令(2026-11-14):「回顧檢視政策 所有系統皆獨立 可獨立完成 為了降低未來 VCGC 升級造成的潛在癱瘓風險」;「照三項開 PR 並盯著」。

依 **L120 ② ④ · L123 ③**:任一系統不在、紅燈或停機,其他系統照常運作;CI 各自一條;`VIA_FROM_VCGC` 的意思已擴為「經四系統任一自己的 manager 或其啟動器啟動」。
本卡只攤開、點名歸屬,不代修他系統;各項由該系統自己的 manager 修。

量測:容器、main @ 1386691d;只讀掃描各系統尾版原始碼(不執行他系統程式)。

---

## 結論

| # | 系統 | 發現 | 證據 | 狀態 / 歸屬 |
|---|---|---|---|---|
| 1 | VDF | CI 的 VDF 合約那條經 VCGC 主控台跑(`CGC_MDL149 run VDF_SystemManager --selftest`,步名 "through the sole entry");VCGC 主控台出錯會連帶 VDF 紅 | `.github/workflows/via-master-control-ui.yml` vdf-uat;L120 ④ 已明令刪除 sole entry 類檢查 | **本 PR 已改**:直接跑 VDF_SystemManager 尾版(同 VRN-2 那條走自己的 MAIN) |
| 2 | VDF | 10 支 VDF 引擎尾版沒有 `VIA_FROM_VCGC=YES` 就拒跑(ENG086 · 094 · 109 · 110×2 · 111 · 112 · 117 · 229 · 231) | 各尾版 `main()` 入口檢查 | **不需改**:VDF 自己的啟動器 `VDF_MDL013_ActivateVDF` 與 `VDF_MDL012_FetchGroups`(v0107 起)替子行程設 `VIA_FROM_VCGC=YES`(註解:舊名 = 經任一系統自己的 manager / 啟動器,L120 ⑥ 甲 / L123 ③),所以經 VDF 自己的入口這 10 支照跑;只有手動單跑才擋 |
| 3 | VRN-2 | 16 支 VRN-2 尾版同樣檢查 `VIA_FROM_VCGC` | 只讀掃描 | **不需改**:`VRN_SystemManager_v0262` 直送引擎時自己 `setdefault("VIA_FROM_VCGC", "YES")`(VRN-2 自己的入口) |
| 4 | VAP | `VAP_SystemManager_v0100` 本身就寫「VCGC is the only caller」,沒有 `VIA_FROM_VCGC=YES` 就拒絕(rc 2) | `functional modules/VAP/VAP_SystemManager_v0100.py` `enter()` | **待 VAP 修(交接)**:與 L125 ①(VAP 有自己的 MAIN、入口 = 各自 SystemManager)不一致;VCGC 不在時 VAP 的入口起不來 |

## 交接項(owner = 各系統 manager)

- **VAP**(owner:VAP_SystemManager):出新版 manager,入口自己認(自己設本系統入口旗標,或照 L123 ③ 自己 `setdefault`),不再要求「只能經 via-vcgc」;自測照改。VCGC 修完後重掃轉態。
- **VDF(可選,文字一致)**:`VDF_SystemManager` 的設定把 `VIA_FROM_VCGC` 列為 `peer_gate_flags`(他系統旗標、不代設),而 VDF 啟動器照 L123 ③ 把它當通用入口旗標設給子行程。行為沒錯,但兩處說法不一致;下次 VDF manager 換版時順手對齊說明即可,不急。

## 不在本卡範圍

- 編號是 L125 規定的唯一跨系統關聯:新東西先空號、VCGC 回來再補(L122 ⑦),VCGC 停擺不卡各系統運作。
- VRN-1 在倉外,只讀。

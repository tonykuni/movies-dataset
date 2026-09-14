# 倉衛生 批506(2026-09-14)

律 L23:只刪有證據的重複件;每筆附 md5 與保留孿生路徑;git 可回溯。

- 刪除 394 件 · 464.0 MB(VAP/ICON_FORGE·ASSETS 同 md5 未被引用孿生 323 · VAP/BACKUP 孿生 71 · 巨檔 sha 副本 0(sha701 被 VAP 規格引用,留))
- BACKUP 保留唯一件 4602

## 未刪(候操作員裁)

- **functional modules/VAP/ICON_FORGE(餘 ~1.1GB,12,3xx 件)** — 1,752 組同 md5 但檔名被 VAP 規格/引擎引用(VIA_VAP_All_Chart_Specs_v017.json 等);刪要先改引用=操作員定
- **functional modules/VAP/ASSETS/SCOPE_COPY(5,273 件)** — 含唯一內容 dict/VRN/_registry(倉內無正本)且 ENG073 v0124 引用;不是純副本
- **supportive modules/VIA_Governance_Runtime/installers/VIAv0162BMaster*.ps1 ×3(22.7MB 各)** — 三檔不同 byte(版本差);runtime_command_center 引用;過時與否=操作員定
- **supportive modules/ui_support 大頁(6~10MB 各:VAP_Compact_Image_Grouping_Report / Fullscreen_HMI_AutoLayoutEditor.before_policy_hotfix / *(standalone)*)** — 正本頁保護(批480 MDL138);before_policy_hotfix 是修前存證;刪=操作員定
- **supportive modules/registry/VIA_ParametersConsolidated_Registry.20260626_173925.dup.csv(25MB)** — 名為 dup 但倉內唯一副本
- **functional modules/VDF/_vdf_system/macro_manifest_fetch_runs(78MB 跑批產出)** — MDL028 產出與 consolidated 同本;跑批存證,刪=操作員定
- **supportive modules/_inbox_to_classify(34MB,611 件,單層巢套)** — 待分類收件夾,非副本

- **VDF_MacroTransformedLong_sha701dd06ad302.json** — VAP 規格以此檔名引用,留(改引用後再刪=操作員定)

## 刪除清單(前 40;全清單見 VIA_RepoHygiene_B506.json)

- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_31_128E5E0ED6__DELETE_CANDIDATE__86393069.svg` md5 8bae59e6 ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593_v2.svg` md5 8bae59e6 ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593_v3.svg` md5 8bae59e6 ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_31_128E5E0ED6__DELETE_CANDIDATE__86393069_v2.svg` md5 8bae59e6 ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_31_128E5E0ED6__DELETE_CANDIDATE__86393069_v3.svg` md5 8bae59e6 ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_31__DUP__128E5E0ED6.svg` md5 8bae59e6 ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_31__DUP__128E5E0ED6_v2.svg` md5 8bae59e6 ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_31__DUP__128E5E0ED6_v3.svg` md5 8bae59e6 ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_31__DUP__128E5E0ED6_v4.svg` md5 8bae59e6 ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_23_128E5E0ED6__DELETE_CANDIDATE__21078593.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_48__DELETE_CANDIDATE__996a986c.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_48_FA5258ED80__DELETE_CANDIDATE__fc02d6bd.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80_v2.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80_v3.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80_v4.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_48__DELETE_CANDIDATE__996a986c_v2.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_48__DELETE_CANDIDATE__996a986c_v3.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_48_FA5258ED80__DELETE_CANDIDATE__fc02d6bd_v2.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_48_FA5258ED80__DELETE_CANDIDATE__fc02d6bd_v3.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_48__DUP__FA5258ED80.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_48__DUP__FA5258ED80_v2.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月2日_下午09_03_48__DUP__FA5258ED80_v3.svg` md5 f05bef48 ← 孿生 `functional modules/VAP/ICON_FORGE/銀色盾徽與拉丁座右銘__FA5258ED80.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_45__DELETE_CANDIDATE__ac56bc62.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_14_16E5CD969F__DELETE_CANDIDATE__27cedc8f.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_45_16E5CD969F__DELETE_CANDIDATE__26488d19.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035_v2.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035_v3.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_45__DELETE_CANDIDATE__ac56bc62_v2.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_45__DELETE_CANDIDATE__ac56bc62_v3.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_14_16E5CD969F__DELETE_CANDIDATE__27cedc8f_v2.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_14_16E5CD969F__DELETE_CANDIDATE__27cedc8f_v3.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_45_16E5CD969F__DELETE_CANDIDATE__26488d19_v2.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_45_16E5CD969F__DELETE_CANDIDATE__26488d19_v3.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_18__DUP__16E5CD969F.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DUP__16E5CD969F.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_45__DUP__16E5CD969F.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_18__DUP__16E5CD969F_v2.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_18__DUP__16E5CD969F_v3.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_18__DUP__16E5CD969F_v4.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DUP__16E5CD969F_v2.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`
- `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DUP__16E5CD969F_v3.svg` md5 0b67b87c ← 孿生 `functional modules/VAP/ICON_FORGE/ChatGPT_Image_2026年4月5日_下午03_57_34__DELETE_CANDIDATE__f74bc035.svg`

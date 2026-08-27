# 批152 收容記(VIA_TW_Grouping_LatestCommand_v0202)

- 來源:操作員批152 附件 `VIA_TW_Grouping_LatestCommand_Package_v0202.zip`
  (sha256 `48a513e23cbee6b0fdebe67e96a24bbad1e2c8201c063deea1032a26ca0ff0d3`,13.7MB)
- 收容:2026-08-25;89 件 byte-exact(`__pycache__` 除外)展開本夾。
- 核心:`VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py`(2,544 行;
  族群歸屬×五指數並行×點時角色輪動;市場門檻由 GMM/BIC+Null 分布動態產生,零寫死)。
  包內 pytest 20 測於本 Linux 環境實跑 **20 passed** 佐證。
- 名冊:`VIA_ThreeList_CanonicalMembershipInput_v0100.csv`(238 檔、39 族群)。
- **RUN_FINAL_V0201/ 不入版控**(40MB 送達方樣跑產物=再生件;循批125
  排除政策,本地保留存證;逐檔 hash 見 `PACKAGE_SHA256_MANIFEST_v0202.json`)。
- 實庫轉接:`engine/GRP_ENG040_GroupingRotationRunner_v0100.py`(via-rotation;
  vdf_tw_market.duckdb→parquet 餵引擎;Windows 預設路徑=原件參考規格,零觸碰)。
  首實跑 2026-08-25:190/238 檔、121,600 列→gate=**PASS**
  (產出 `output_hub/rotation_runs/`,gitignored)。

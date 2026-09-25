# VIA 倉衛生 批511(併線去重)

> 律:L23 只刪 byte 同(git blob 同 sha)且路徑/檔名未被引用的重複件;留存件在既有正式夾;側枝 local/parallel-b508-09151416 保有全份

## 量到

- 併入側枝 `local/parallel-b508-09151416`(= 操作員機器 main 8071a062 + 並行線 7cc9031f)相對本線 HEAD 新增 734 件(不含 .via_envmanager);其中 **374 件與倉內既有檔 git blob 同 sha(byte 同)**、48 件彼此同 sha、312 件獨有內容。
- `.via_envmanager/`:65 檔 163 MB(env_report.json 38 MB、runs/round_1~3.json 各 35 MB、60 個 snapshots)= EnvManager 執行期狀態 → **不入倉**(.gitignore 已加;側枝保有全份)。

## 刪(只刪 byte 同且路徑/檔名未被引用者;45 件;留存件合計 1.8 MB)

| 群 | 件數 |
|---|---|
| new modules engines/VeritasPulse_v14 | 15 |
| new modules engines/VDF_final | 13 |
| functional modules/VAP | 6 |
| new modules engines/taiwan_revenue_engine | 4 |
| supportive modules/output | 2 |
| new modules engines/VRN_MDL006_ConsolidatorAndPhaseValidator (3).py | 1 |
| new modules engines/VRN_MDL008_CrossValidator (2).py | 1 |
| new modules engines/VRN_PIPELINE_LAUNCHER (1).ps1 | 1 |
| new modules engines/VRN_Pipeline_Runner (3).py | 1 |
| new modules engines/族群分類方法.docx | 1 |

## 留(byte 同但路徑或檔名被引用=不刪;377 件)

| 群 | 件數 |
|---|---|
| functional modules/VAP | 184 |
| new modules engines/Icons | 160 |
| new modules engines/VeritasPulse_v14 | 16 |
| new modules engines/VDF_final | 3 |
| new modules engines/taiwan_revenue_engine | 3 |
| CGE/Console | 1 |
| new modules engines/VIA_CentralGovernanceConsole (2).py | 1 |
| new modules engines/VIA_CentralGovernanceEngine (2).py | 1 |
| new modules engines/VIA_DownwardController (2).py | 1 |
| new modules engines/VIA_DownwardController (3).py | 1 |
| new modules engines/VIA_DownwardController (4).py | 1 |
| new modules engines/VIA_FilePriorityRouter (1).py | 1 |

## 候裁(不刪)

- 獨有內容 312 件一律留(只增):`functional modules/VAP` 123、`new modules engines/VeritasPulse_v14` 34、`VDF_final` 30、`VIA_ActiveETF_FINAL (1)` 19、`taiwan_revenue_engine` 11、`版本管理` 8、並行線 VRN/VDF 引擎 22。
- `new modules engines/*` = 另一條線的引擎收容件(檔名帶 (2)/(3) 的副本病);建議下一批入 `references/intake` 並冊上,再由尾版律決定誰是正本。

## 每筆刪除證據

| 刪 | md5 | 留存孿生 |
|---|---|---|
| `functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder.py.bak_intel_v3_20260506_220341` | `52157d31c05d8567818c0521d3cffbe2` | `functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder.py.bak_intel_v3_20260506_220341` |
| `functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder.py.bak_optimize_20260506_215526` | `a990d7d6965263c4ea2f12c7e4c8e754` | `functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder.py.bak_optimize_20260506_215526` |
| `functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder.py.bak_optimize_v2_20260506_215846` | `a990d7d6965263c4ea2f12c7e4c8e754` | `functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder.py.bak_optimize_20260506_215526` |
| `functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder.py.bak_quotehard_20260506_214620` | `5bcf64928b6976be086671a0eb28251e` | `functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder.py.bak_quotehard_20260506_214620` |
| `functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder.py.bak_regex_20260506_213820` | `fced47bea6564798e26bd1360aa1cc80` | `functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder.py.bak_regex_20260506_213820` |
| `functional modules/VAP/ui/VIA_VAP_System_sha48bfc00a.html` | `7992f961a2bc99f876d2bdfb091b2be6` | `functional modules/VAP/ui/VIA_VAP_System.html` |
| `new modules engines/VDF_final/config/tw_consensus_ssot.json` | `e63248814d4e0364d0e0f7cb1b351c37` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/tw_consensus_ssot.json` |
| `new modules engines/VDF_final/logs/.gitkeep` | `d41d8cd98f00b204e9800998ecf8427e` | `functional modules/GroupIndex/db/.gitkeep` |
| `new modules engines/VDF_final/src/vdf_bridge.py` | `d4bb98df0f2cede784b88321707a5395` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_bridge.py` |
| `new modules engines/VDF_final/src/vdf_fetchers_consensus.py` | `211010ee4a9fa4ceaaf2194891c717da` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_consensus.py` |
| `new modules engines/VDF_final/src/vdf_fetchers_derived.py` | `e09783dd1dd75eabe2c2e7f4dea0417a` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_derived.py` |
| `new modules engines/VDF_final/src/vdf_fetchers_etf_holdings.py` | `291480711d134a9d06336e14d4de4fd4` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_etf_holdings.py` |
| `new modules engines/VDF_final/src/vdf_fetchers_fed.py` | `d8e4b891af988bf97a0ca534b373eec5` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_fed.py` |
| `new modules engines/VDF_final/src/vdf_fetchers_financials.py` | `23140c6df7215ba4c93fd7c81a0a9412` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_financials.py` |
| `new modules engines/VDF_final/src/vdf_fetchers_fiscal.py` | `9a3f32cbf6041a14a81d7633ab84121e` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_fiscal.py` |
| `new modules engines/VDF_final/src/vdf_fetchers_market.py` | `98ac25f5943788ce676274dd4a21eaf4` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_market.py` |
| `new modules engines/VDF_final/src/vdf_fetchers_sentiment.py` | `e1fe856ef632992742f6de43ad03ab59` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_sentiment.py` |
| `new modules engines/VDF_final/src/vdf_fetchers_tdcc.py` | `9573091eb08aadf1fc421cfa948786ba` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_tdcc.py` |
| `new modules engines/VDF_final/src/vdf_supportive_bridge.py` | `5438ede2bee4b2473e500ec919f08cff` | `functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_supportive_bridge.py` |
| `new modules engines/VRN_MDL006_ConsolidatorAndPhaseValidator (3).py` | `3cd3e00ab4b4d61f563918bf18f410c5` | `supportive modules/references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VRN_MDL006_ConsolidatorAndPhaseValidator (3).py` |
| `new modules engines/VRN_MDL008_CrossValidator (2).py` | `3f4da152fc15d5d7a4faecac3e89acf6` | `supportive modules/references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VRN_MDL008_CrossValidator (2).py` |
| `new modules engines/VRN_PIPELINE_LAUNCHER (1).ps1` | `9a2e37c516101038f3a01d566fd24a80` | `supportive modules/references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VRN_PIPELINE_LAUNCHER (1).ps1` |
| `new modules engines/VRN_Pipeline_Runner (3).py` | `d41af28af94e77e1b7c9d9d744c4a1ed` | `supportive modules/references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VRN_Pipeline_Runner (3).py` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/PACKAGING.md` | `56fb5a2d2f7421b99976ca78bdf384ad` | `functional modules/WorkOps/VeritasPulse/PACKAGING.md` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/README.md` | `3d8661b178406d571fced6296adda0b0` | `functional modules/WorkOps/VeritasPulse/README.md` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/VRN_Meeting_Minutes.pdf` | `a46c61bedf2308f4593a44d0c81233c8` | `functional modules/WorkOps/VeritasPulse/output/VRN_Meeting_Minutes.pdf` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/manifest.webmanifest` | `f02277fd0e32d06e20ff45f4bf966811` | `functional modules/WorkOps/VeritasPulse/output/manifest.webmanifest` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/minutes.json` | `349cd2ff2cee3c184bba269482bac8b7` | `functional modules/WorkOps/VeritasPulse/output/minutes.json` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/news_source.json` | `09932e555c2f219858b13977ae9c3399` | `functional modules/WorkOps/VeritasPulse/output/news_source.json` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/plan.json` | `cc7cfe2499e9b3e2c084071609f06864` | `functional modules/WorkOps/VeritasPulse/output/plan.json` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/service-worker.js` | `63fee1d631179d9c1a23e635504c073d` | `functional modules/WorkOps/VeritasPulse/output/service-worker.js` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/stakeholder.json` | `954a82726a78209e77c89559517e0c26` | `functional modules/WorkOps/VeritasPulse/output/stakeholder.json` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/team.json` | `72449fd6198912206ffec7220350e1fb` | `functional modules/WorkOps/VeritasPulse/output/team.json` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/warehouse/news_source.json` | `09932e555c2f219858b13977ae9c3399` | `functional modules/WorkOps/VeritasPulse/output/news_source.json` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/warehouse/plan.json` | `cc7cfe2499e9b3e2c084071609f06864` | `functional modules/WorkOps/VeritasPulse/output/plan.json` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/warehouse/stakeholder.json` | `954a82726a78209e77c89559517e0c26` | `functional modules/WorkOps/VeritasPulse/output/stakeholder.json` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/output/warehouse/team.json` | `72449fd6198912206ffec7220350e1fb` | `functional modules/WorkOps/VeritasPulse/output/team.json` |
| `new modules engines/VeritasPulse_v14/VeritasPulse/requirements.txt` | `4b69844d48f07f1970fbb66524a6cf00` | `functional modules/WorkOps/VeritasPulse/requirements.txt` |
| `new modules engines/taiwan_revenue_engine/README.md` | `5a1c8e467dd57ac09e767182fa2ec4d7` | `functional modules/GroupIndex/engine/taiwan_revenue_engine/README.md` |
| `new modules engines/taiwan_revenue_engine/config.yaml` | `fb65d05109769c62640b0f23776409a1` | `functional modules/GroupIndex/engine/taiwan_revenue_engine/config.yaml` |
| `new modules engines/taiwan_revenue_engine/output/sample_dashboard.html` | `b3c2f479cccdad5b4c0f1364bba249fc` | `functional modules/GroupIndex/engine/taiwan_revenue_engine/package_samples/output/monthly_revenue_dashboard.html` |
| `new modules engines/taiwan_revenue_engine/requirements.txt` | `c82361a562b59d48b257180cdc9f07b6` | `functional modules/GroupIndex/engine/taiwan_revenue_engine/requirements.txt` |
| `new modules engines/族群分類方法.docx` | `5e8fcd3d3b0e6a7f45a3cab153331d5f` | `functional modules/GroupIndex/curated/VIA_GroupIndex_Methodology_Dialogue_20260819.docx` |
| `supportive modules/output/manifest.webmanifest` | `f02277fd0e32d06e20ff45f4bf966811` | `functional modules/WorkOps/VeritasPulse/output/manifest.webmanifest` |
| `supportive modules/output/service-worker.js` | `63fee1d631179d9c1a23e635504c073d` | `functional modules/WorkOps/VeritasPulse/output/service-worker.js` |

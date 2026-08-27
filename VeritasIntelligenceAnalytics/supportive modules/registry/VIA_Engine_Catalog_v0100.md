# VIA 引擎總目錄 v0100(逐引擎詳細功能)

引擎 352 支 · 20260818_101916 · 原則:零發明:說明=AST 實抽 docstring;函式/CLI/邊=合約冊實值

| SYS | 支數 | 自測具備 |
|---|---|---|
| CHW · 籌碼戰 | 26 | 0 |
| FLOW · 資金流 | 18 | 0 |
| GRP · 族群指數 | 38 | 3 |
| PLG · 插件 | 18 | 0 |
| VAP · 視覺分析 | 3 | 0 |
| VDF · 數據鍛造 | 42 | 1 |
| VIA · 泛功能 | 147 | 1 |
| VRN · 報告情報 | 60 | 4 |

## CHW · 籌碼戰(26 支)

### CHW_ENG001_ChipWarConsole
- **族**:`functional modules/ChipWar/engines/VIA_ChipWar_Console`(版本 1;現役 `VIA_ChipWar_Console_v010.py`)
- **功能**:VIA_ChipWar_Console_v010.py
- **函式**(5):`run_engine(name, meta)` · `phase_test()` · `phase_consolidate(results)` · `phase_user_test()` · `main()`
- **自測**:主程式可跑

### CHW_ENG002_FinMindIngest
- **族**:`functional modules/ChipWar/engines/VIA_FinMind_Ingest`(版本 1;現役 `VIA_FinMind_Ingest_v010.py`)
- **功能**:VIA_FinMind_Ingest_v010.py
- **函式**(12):`init_db(con)` · `t_plus_1(d)` · `raw_hash(obj)` · `fetch_live(ds, stock_id, start, end)` · `fetch_mock(ds, stock_id, start, end)` · `fetch(ds, stock_id, start, end)` · `validate(name, df)` · `normalize(name, raw)` · `ingest(con, name, start, end)` · `derive_gov_net(con)`
- **自測**:主程式可跑

### CHW_ENG003_ForeignGameEngine
- **族**:`functional modules/ChipWar/engines/VIA_ForeignGameEngine`(版本 1;現役 `VIA_ForeignGameEngine.py`)
- **功能**:VIA_ForeignGameEngine.py — 外資級聯博弈引擎 (宏觀→外資→內資)
- **函式**(7):`z(s, w, lag, mn)` · `gen_world(seed)` · `classify(df)` · `lead_lag(a, b, maxlag)` · `evaluate(seed)` · `run_tests()` · `main()`
- **自測**:主程式可跑

### CHW_ENG004_GovFundEngine
- **族**:`functional modules/ChipWar/engines/VIA_GovFundEngine`(版本 1;現役 `VIA_GovFundEngine_v040.py`)
- **功能**:VIA_GovFundEngine_v040.py — 自主進化版
- **函式**(12):`gen_world(world, n, seed)` · `z(s, w, mp)` · `build(df, dd_q)` · `score(out, use)` · `detect(out, zc, use)` · `fuzzy(t, k)` · `recall_fpr(sig, truth)` · `loeo(df, use)` · `ablate(df, use, zc)` · `auto_select()`
- **自測**:主程式可跑

### CHW_ENG005_RotationEngine
- **族**:`functional modules/ChipWar/engines/VIA_RotationEngine`(版本 1;現役 `VIA_RotationEngine_v010.py`)
- **功能**:VIA_RotationEngine_v010.py
- **函式**(11):`z(s, w, lag)` · `roc(s, lag)` · `gen_world(seed)` · `build_panel(dates, mkt, flows, prices)` · `quadrant(fm, pm)` · `alerts_for(panel)` · `daily_ic(sig, fwd)` · `ic_t(ics)` · `backtest(seed)` · `run_tests()`
- **自測**:主程式可跑

### CHW_ENG006_RotationDashboard
- **族**:`functional modules/ChipWar/engines/VIA_Rotation_Dashboard`(版本 1;現役 `VIA_Rotation_Dashboard.py`)
- **功能**:VIA_Rotation_Dashboard.py — 族群資金輪動視覺化 · RRG象限圖 · Visual Lock
- **函式**(7):`esc(s)` · `load_points()` · `def_rrg_svg(pts)` · `def_alert_rows(pts)` · `def_error_rows()` · `def_build(pts)` · `main()`
- **自測**:主程式可跑

### CHW_ENG007_SectorWhaleEngine
- **族**:`functional modules/ChipWar/engines/VIA_SectorWhaleEngine`(版本 1;現役 `VIA_SectorWhaleEngine_v020.py`)
- **功能**:VIA_SectorWhaleEngine_v020.py — 準確率改良 + 完整回測(準確率/波動性)
- **函式**(9):`gen_world(seed, n)` · `zscore(s, kind, w, mp, lag)` · `sector_flows(df)` · `anchor_asof(wkdf, sec, dates)` · `detect(flow_z, anchor, cfg)` · `fuzzy(t, k)` · `metrics(sig, truth_dir)` · `backtest(cfg)` · `main()`
- **自測**:主程式可跑

### CHW_ENG008_PurifiedSectorRotationAccuracyEngineV2
- **族**:`functional modules/ChipWar/engines/purified_sector_rotation_accuracy_engine_v2`(版本 1;現役 `purified_sector_rotation_accuracy_engine_v2.py`)
- **功能**:無說明(候補)
- **類**:UltraAccuracyEngineV2
- **自測**:主程式可跑

### CHW_ENG009_SectorRotationCapitalFlowEngine
- **族**:`functional modules/ChipWar/engines/sector_rotation_capital_flow_engine`(版本 1;現役 `sector_rotation_capital_flow_engine.py`)
- **功能**:無說明(候補)
- **類**:SectorRotationEngine
- **函式**(1):`generate_noisy_market_data(days)`
- **自測**:主程式可跑

### CHW_ENG010_SsotMatchingTestingEngine
- **族**:`functional modules/ChipWar/engines/ssot_matching_testing_engine`(版本 1;現役 `ssot_matching_testing_engine.py`)
- **功能**:無說明(候補)
- **類**:UniversalSchemaNeutralizer, SSOTMatchingEngine
- **函式**(1):`run_engine_tests()`
- **自測**:主程式可跑

### CHW_ENG011_ViaEngineVerificationSuite
- **族**:`functional modules/ChipWar/engines/veritas_via_engine_verification_suite`(版本 1;現役 `veritas_via_engine_verification_suite.py`)
- **功能**:無說明(候補)
- **類**:VeritasViaTestSuite
- **自測**:主程式可跑

### CHW_ENG012_ViaExactDatasetTestEngine
- **族**:`functional modules/ChipWar/engines/veritas_via_exact_dataset_test_engine`(版本 1;現役 `veritas_via_exact_dataset_test_engine.py`)
- **功能**:無說明(候補)
- **類**:RecordDatasetTester
- **自測**:主程式可跑

### CHW_ENG013_ViaSystemIntegrationTestSuite
- **族**:`functional modules/ChipWar/engines/veritas_via_system_integration_test_suite`(版本 1;現役 `veritas_via_system_integration_test_suite_v0101.py`)
- **功能**:無說明(候補)
- **類**:VeritasViaSystemIntegrationTester
- **自測**:主程式可跑

### CHW_ENG014_BlocEngine
- **族**:`functional modules/ChipWar/engines/via_bloc_engine`(版本 1;現役 `via_bloc_engine.py`)
- **功能**:VIA Bloc Concentration Lane v0.1 — 選擇有限 (limited choices): tech vs traditional
- **自測**:匯入型

### CHW_ENG015_ChipwarEngine
- **族**:`functional modules/ChipWar/engines/via_chipwar_engine`(版本 1;現役 `via_chipwar_engine.py`)
- **功能**:VIA ChipWar Chain Head (T4 placeholder) — 合成宇宙 + regime
- **自測**:匯入型

### CHW_ENG016_ChipwarVapDashboard
- **族**:`functional modules/ChipWar/engines/via_chipwar_vap_dashboard`(版本 1;現役 `via_chipwar_vap_dashboard.py`)
- **功能**:VIA ChipWar × VAP 儀表板 v0100 — 全鏈成果 → VAP 28 型圖庫(擴充功能整合層)
- **函式**(3):`fail(msg)` · `col(rows, key)` · `clean(dates, fields)`
- **自測**:匯入型

### CHW_ENG017_FomoIndexEngine
- **族**:`functional modules/ChipWar/engines/via_fomo_index_engine`(版本 1;現役 `via_fomo_index_engine.py`)
- **功能**:VIA FOMO Index v0.1 — 統一 FOMO 指數 (0-100)
- **自測**:匯入型

### CHW_ENG018_FomoIndexReport
- **族**:`functional modules/ChipWar/engines/via_fomo_index_report`(版本 1;現役 `via_fomo_index_report.py`)
- **功能**:FOMO Index report — Visual Lock + FlowSystem verdict style.
- **函式**(3):`gauge(v, W, H)` · `norm(x)` · `line_chart(W, H)`
- **自測**:匯入型

### CHW_ENG019_MacroEngine
- **族**:`functional modules/ChipWar/engines/via_macro_engine`(版本 1;現役 `via_macro_engine.py`)
- **功能**:VIA Macro Liquidity Lane v0.1 — 資金盤根因層
- **函式**(2):`asof_monthly(day)` · `lag_weekly(x, lag)`
- **自測**:匯入型

### CHW_ENG020_RotationPlugInEngine
- **族**:`functional modules/ChipWar/engines/via_rotation_plug_in_engine`(版本 1;現役 `via_rotation_plug_in_engine.py`)
- **功能**:無說明(候補)
- **類**:VIARotationPluginEngine
- **自測**:主程式可跑

### CHW_ENG021_SocialEngine
- **族**:`functional modules/ChipWar/engines/via_social_engine`(版本 1;現役 `via_social_engine.py`)
- **功能**:VIA Social FOMO Lane v0.1 — 聊天室 FOMO 第二通道
- **自測**:匯入型

### CHW_ENG022_SocialReport
- **族**:`functional modules/ChipWar/engines/via_social_report`(版本 1;現役 `via_social_report.py`)
- **功能**:Social FOMO lane report — Visual Lock.
- **函式**(3):`norm(x)` · `svg_line(series, W, H, x0, x1)` · `svg_ccf(df, W, H)`
- **自測**:匯入型

### CHW_ENG023_TestHarness
- **族**:`functional modules/ChipWar/engines/via_test_harness`(版本 1;現役 `via_test_harness.py`)
- **功能**:VIA Engine Test Harness  —  跑全鏈 + 驗證每支輸出 + 魔鬼批判檢查
- **函式**(2):`has_nan(obj)` · `run_one(engine, outjson, req)`
- **CLI**:`--mode` `--out`
- **自測**:匯入型

### CHW_ENG024_XmktEngine
- **族**:`functional modules/ChipWar/engines/via_xmkt_engine`(版本 1;現役 `via_xmkt_engine.py`)
- **功能**:VIA Cross-Market FOMO Factor Lab v0.1 — 台灣 FOMO 因子組 → ^TWII + ^GSPC
- **函式**(2):`zsc(v)` · `walkforward(tgt_col, criteria)`
- **自測**:匯入型

### CHW_ENG025_XmktReport
- **族**:`functional modules/ChipWar/engines/via_xmkt_report`(版本 1;現役 `via_xmkt_report.py`)
- **功能**:Cross-market FOMO factor lab report — Visual Lock.
- **函式**(1):`heat(target, title)`
- **自測**:匯入型

### CHW_ENG026_CodeArtifact3
- **族**:`functional modules/ChipWar/engines/code_artifact_3`(版本 1;現役 `code_artifact_3.py`)
- **功能**:無說明(候補)
- **類**:VolumeDrivenRotationEngine
- **自測**:主程式可跑


## FLOW · 資金流(18 支)

### FLOW_ENG001_FlowAutotest
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_autotest`(版本 1;現役 `flow_autotest.py`)
- **功能**:VDF-FLOW-AUTOTEST flow_autotest.py — 硬化+引擎建構驗證(v0100R)。
- **函式**(1):`run()`
- **自測**:主程式可跑

### FLOW_ENG002_FlowBridge
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_bridge`(版本 1;現役 `flow_bridge.py`)
- **功能**:VDF-FLOW-BRIDGE flow_bridge.py — 真實資料入口(v0101R)。
- **函式**(5):`load_daily()` · `load_perf_prices()` · `load_flow_precise()` · `load_reference_flows()` · `source_status()`
- **自測**:匯入型

### FLOW_ENG003_FlowCalibrate
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_calibrate`(版本 1;現役 `flow_calibrate.py`)
- **功能**:CALIBRATE-13 flow_calibrate.py — optimize→test→debug→backtest→calibrate 迴圈(v0100R)。
- **函式**(1):`calibrate(panel, params, write)`
- **自測**:匯入型

### FLOW_ENG004_FlowCore
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_core`(版本 1;現役 `flow_core.py`)
- **功能**:VDF-FLOW-CORE-11 flow_core.py — FIS 強度 + 雙估計器信任 + 聚合(v0100R 重建版)。
- **函式**(9):`load_json(p, default)` · `load_params()` · `load_universe()` · `compute_fis(panel, params, universe)` · `role_gate(rows, universe)` · `bucket_fis(rows, key_fn, params, universe)` · `gram(rows, params, universe)` · `roro(rows, params, universe)` · `snapshot(rows, params, universe)`
- **自測**:匯入型

### FLOW_ENG005_FlowFactors
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_factors`(版本 1;現役 `flow_factors.py`)
- **功能**:VDF-FLOW-FACTORS flow_factors.py — 因子庫(v0100R)。
- **函式**(1):`build_factors(rows, rets_fwd, min_t, include_noise_probe, seed)`
- **自測**:匯入型

### FLOW_ENG006_FlowGrid
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_grid`(版本 1;現役 `flow_grid.py`)
- **功能**:VDF-FLOW-GRID-22 flow_grid.py — Region×Sector 網格 + Fidelity 評分卡(v0100R)。
- **函式**(1):`build_grid(rows, write)`
- **自測**:匯入型

### FLOW_ENG007_FlowHub
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_hub`(版本 1;現役 `flow_hub.py`)
- **功能**:VDF-FLOW-HUB flow_hub.py — 單一視窗整合 Hub + 理論總覽(v0101R;操作員「介面整合」令)。
- **函式**(5):`svg_main_flow()` · `svg_quadrant()` · `svg_solid()` · `svg_engine_layers()` · `build_hub(write)`
- **自測**:匯入型

### FLOW_ENG008_FlowMacro
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_macro`(版本 1;現役 `flow_macro.py`)
- **功能**:VDF-FLOW-MACRO flow_macro.py — 宏觀對照層 v2(自適應權重;操作員 2026/08/12 令)。
- **函式**(1):`load_macro_cfg()`
- **自測**:匯入型

### FLOW_ENG009_FlowManager
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_manager`(版本 1;現役 `flow_manager.py`)
- **功能**:MANAGER-15 flow_manager.py — 系統管理/編排 + synth + CLI(v0100R)。
- **函式**(4):`cmd_synth(rho_override)` · `cmd_run(live)` · `cmd_status()` · `main()`
- **自測**:主程式可跑

### FLOW_ENG010_FlowMonitor
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_monitor`(版本 1;現役 `flow_monitor.py`)
- **功能**:VDF-FLOW-MONITOR flow_monitor.py — 族群整合監控 + 採用項目專頁(v0100R)。
- **函式**(1):`build_monitor(rows, write)`
- **自測**:匯入型

### FLOW_ENG011_FlowPerf
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_perf`(版本 1;現役 `flow_perf.py`)
- **功能**:VDF-FLOW-PERF flow_perf.py — 正規化走勢圖 + 主題分類(v0100R)。
- **函式**(1):`build_perf(write)`
- **自測**:匯入型

### FLOW_ENG012_FlowPillarA
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_pillar_a`(版本 1;現役 `flow_pillar_a.py`)
- **功能**:PILLARA-19 flow_pillar_a.py — Pillar A 測量校準(v0100R)。
- **函式**(1):`validate_a(fis_rows, write)`
- **自測**:匯入型

### FLOW_ENG013_FlowRoles
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_roles`(版本 1;現役 `flow_roles.py`)
- **功能**:VDF-FLOW-ROLES flow_roles.py — monitor_role 閘門 + 分類存取(v0100R)。
- **函式**(5):`spot_only(rows, universe)` · `by_tier(universe)` · `by_region(universe)` · `by_class(universe)` · `fidelity_classes(universe)`
- **自測**:匯入型

### FLOW_ENG014_FlowSelftest
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_selftest`(版本 1;現役 `flow_selftest.py`)
- **功能**:SELFTEST-20 flow_selftest.py — 14 項邊界測試(v0100R;README v0103 涵蓋清單)。
- **函式**(1):`run()`
- **自測**:主程式可跑

### FLOW_ENG015_FlowSim
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_sim`(版本 1;現役 `flow_sim.py`)
- **功能**:VDF-FLOW-SIM flow_sim.py — 全球資金流動情境模擬引擎(v0100R)。
- **函式**(4):`load_sim()` · `ground_loadings(rows, universe)` · `build_frames(sim, loadings, src)` · `build_map_sim(rows, write)`
- **自測**:匯入型

### FLOW_ENG016_FlowUi
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_ui`(版本 1;現役 `flow_ui.py`)
- **功能**:UI-14 flow_ui.py — 由 JSON 產 Visual Lock index.html(v0100R)。
- **函式**(8):`esc(s)` · `css_base()` · `nav_strip(current)` · `macro_card(mo)` · `vr_card(mo)` · `why_card(mo)` · `gaps_card(mo)` · `build_index(rows, calib, status, grid, factors)`
- **自測**:匯入型

### FLOW_ENG017_FlowValidate
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_validate`(版本 1;現役 `flow_validate.py`)
- **功能**:VALIDATE-12 flow_validate.py — IC/decay/quantile/long-short/null + gate 評估(v0100R)。
- **函式**(8):`rank_ic(sig, fwd)` · `daily_ic(rows, rets)` · `hac_t(ics, lags)` · `quantile_check(rows, rets, q)` · `long_short(rows, rets, cost_bps, q)` · `null_test(rows, rets, k, seed)` · `lead_ratio(rows, rets_fwd, rets_same)` · `evaluate(rows, rets_fwd, rets_same, params)`
- **自測**:匯入型

### FLOW_ENG018_FlowWorldmap
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_worldmap`(版本 1;現役 `flow_worldmap.py`)
- **功能**:VDF-FLOW-WORLDMAP-23 flow_worldmap.py — 世界地圖/風險階梯 資金流動畫(v0100R)。
- **函式**(2):`build_worldmap(rows, write)` · `build_tierflow(rows, write)`
- **自測**:匯入型


## GRP · 族群指數(38 支)

### GRP_ENG001_ActiveStockETF
- **族**:`functional modules/GroupIndex/engine/VIA_ActiveStockETF`(版本 1;現役 `VIA_ActiveStockETF.py`)
- **功能**:VIA_ActiveStockETF.py
- **類**:Log, FetchError, Http, Val, Sources, Registry
- **函式**(12):`decode_text(raw)` · `roc_to_iso(s)` · `to_float(v)` · `to_int(v)` · `norm_text(s)` · `today_tw()` · `month_starts(months, end)` · `parse_isin_table(html_text)` · `parse_nav_rows(rows)` · `parse_stock_day_rows(rows)`
- **CLI**:`---` `--base-isin` `--base-openapi` `--base-tpex` `--base-twse` `--cache` `--months` `--no-cache` `--offline` `--open` `--out` `--overrides`
- **自測**:✅ --selftest

### GRP_ENG002_ActiveStockETFMocktest
- **族**:`functional modules/GroupIndex/engine/VIA_ActiveStockETF_mocktest`(版本 1;現役 `VIA_ActiveStockETF_mocktest.py`)
- **功能**:VIA_ActiveStockETF_mocktest.py
- **類**:MockMarket, MockServer
- **函式**(12):`iso_to_roc(iso)` · `trading_days(n, end)` · `check(name, cond, detail)` · `run_engine(server, out, extra)` · `load_out(out)` · `scenario_cold_start(out, today)` · `scenario_new_listing(out, today)` · `scenario_delisting(out, today)` · `scenario_degraded(out, today)` · `scenario_cache_offline(out, today)`
- **CLI**:`--base-isin` `--base-openapi` `--base-tpex` `--base-twse` `--keep` `--months` `--no-cache` `--offline` `--out` `--quiet` `--workers`
- **自測**:主程式可跑

### GRP_ENG003_ChipWarConsole
- **族**:`functional modules/GroupIndex/engine/VIA_ChipWar_Console`(版本 1;現役 `VIA_ChipWar_Console_v010.py`)
- **功能**:VIA_ChipWar_Console_v010.py
- **函式**(5):`run_engine(name, meta)` · `phase_test()` · `phase_consolidate(results)` · `phase_user_test()` · `main()`
- **自測**:主程式可跑

### GRP_ENG004_ChipWarRevenueEvidence
- **族**:`functional modules/GroupIndex/engine/VIA_ChipWar_Revenue_Evidence`(版本 1;現役 `VIA_ChipWar_Revenue_Evidence_v0100.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **函式**(3):`sha256(path)` · `def_run(label, args, cwd, token)` · `def_main()`
- **自測**:主程式可跑

### GRP_ENG005_ETFConsolesEvidence
- **族**:`functional modules/GroupIndex/engine/VIA_ETF_Consoles_Evidence`(版本 1;現役 `VIA_ETF_Consoles_Evidence_v0100.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **函式**(3):`sha256(path)` · `def_run_check(spec)` · `def_main()`
- **CLI**:`--mocktest` `--selftest`
- **自測**:✅ --selftest

### GRP_ENG006_FinMindIngest
- **族**:`functional modules/GroupIndex/engine/VIA_FinMind_Ingest`(版本 1;現役 `VIA_FinMind_Ingest_v010.py`)
- **功能**:VIA_FinMind_Ingest_v010.py
- **函式**(12):`init_db(con)` · `t_plus_1(d)` · `raw_hash(obj)` · `fetch_live(ds, stock_id, start, end)` · `fetch_mock(ds, stock_id, start, end)` · `fetch(ds, stock_id, start, end)` · `validate(name, df)` · `normalize(name, raw)` · `ingest(con, name, start, end)` · `derive_gov_net(con)`
- **自測**:主程式可跑

### GRP_ENG007_GlobalETFFlow
- **族**:`functional modules/GroupIndex/engine/VIA_GlobalETFFlow`(版本 1;現役 `VIA_GlobalETFFlow.py`)
- **功能**:VIA_GlobalETFFlow.py
- **類**:Log, FetchError, Http, Val, Sources, _RobustWindow, UniverseRegistry, SharesRegistry
- **函式**(10):`decode_text(raw)` · `to_float(v)` · `median(xs)` · `mad(xs, med)` · `robust_z(x, sample)` · `clamp(x, lo, hi)` · `today_utc()` · `parse_stooq_csv(text)` · `parse_yahoo_chart(doc)` · `parse_quote_summary(doc)`
- **CLI**:`--all` `--base-stooq` `--base-yahoo` `--cache` `--group` `--keep` `--mocktest` `--no-cache` `--offline` `--open` `--out` `--probe`
- **自測**:✅ --selftest

### GRP_ENG008_GovFundEngine
- **族**:`functional modules/GroupIndex/engine/VIA_GovFundEngine`(版本 1;現役 `VIA_GovFundEngine_v040.py`)
- **功能**:VIA_GovFundEngine_v040.py — 自主進化版
- **函式**(12):`gen_world(world, n, seed)` · `z(s, w, mp)` · `build(df, dd_q)` · `score(out, use)` · `detect(out, zc, use)` · `fuzzy(t, k)` · `recall_fpr(sig, truth)` · `loeo(df, use)` · `ablate(df, use, zc)` · `auto_select()`
- **自測**:主程式可跑

### GRP_ENG009_GroupIndexEnvPreflight
- **族**:`functional modules/GroupIndex/engine/VIA_GroupIndex_EnvPreflight`(版本 1;現役 `VIA_GroupIndex_EnvPreflight_v0100.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **函式**(7):`def_detect_env()` · `def_check_tools()` · `def_discover_via_envs()` · `def_audit_base_cleanliness()` · `def_whitelist_gap()` · `def_run_preflight(enforce)` · `main(argv)`
- **CLI**:`--enforce`
- **自測**:主程式可跑

### GRP_ENG010_GroupIndexMasterValidation
- **族**:`functional modules/GroupIndex/engine/VIA_GroupIndex_MasterValidation`(版本 1;現役 `VIA_GroupIndex_MasterValidation_v0100.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **函式**(3):`sha256(path)` · `def_run_master_validation()` · `main()`
- **自測**:主程式可跑

### GRP_ENG011_LiveWireContractAdapter
- **族**:`functional modules/GroupIndex/engine/VIA_LiveWire_ContractAdapter`(版本 1;現役 `VIA_LiveWire_ContractAdapter_v0100.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **類**:MatchResult, FetchStatus, HonestMarketDataFetcher
- **函式**(8):`def_validate_ticker(ticker)` · `def_normalize_stock_entry(raw)` · `def_normalize_database(raw_db)` · `def_name_similarity(a, b)` · `def_reconcile_against_local(mother_raw, local_members, similarity_threshold)` · `def_validate_panel_contract(panel)` · `def_load_local_ssot_members(ssot_path)` · `def_run_adapter_evidence(out_dir)`
- **自測**:主程式可跑

### GRP_ENG012_SectorFlowAdaptiveChainedIndex
- **族**:`functional modules/GroupIndex/engine/VIA_SectorFlow_AdaptiveChainedIndex`(版本 1;現役 `VIA_SectorFlow_AdaptiveChainedIndex_v0100.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **類**:PipelineConfig
- **函式**(12):`def_configure_cjk_font()` · `def_now()` · `def_sha256(path)` · `def_stable_seed(text)` · `def_write_csv(df, path)` · `def_write_json(obj, path)` · `def_digest_frame(df)` · `def_add_phase(rows, phase, status, detail, started)` · `def_add_test(rows, test_id, name, status, severity)` · `def_html_table(df, max_rows)`
- **CLI**:`--no-activate` `--no-plots` `--out-dir` `--plot-dir` `--run-tag` `--ssot`
- **自測**:主程式可跑

### GRP_ENG013_SectorFlowDashboardBuilder
- **族**:`functional modules/GroupIndex/engine/VIA_SectorFlow_Dashboard_Builder`(版本 1;現役 `VIA_SectorFlow_Dashboard_Builder_v0100.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **函式**(6):`r2(x)` · `r4(x)` · `def_vap_ticks(lo, hi)` · `def_write_vap_compliance()` · `def_build_payload()` · `main()`
- **自測**:主程式可跑

### GRP_ENG014_SectorFlowSignalTradeBacktest
- **族**:`functional modules/GroupIndex/engine/VIA_SectorFlow_SignalTradeBacktest`(版本 1;現役 `VIA_SectorFlow_SignalTradeBacktest_v0100.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **函式**(12):`def_load_base_engine()` · `def_prepare_trade_panel(base, result)` · `def_simulate_group_trades(g)` · `def_run_trade_simulation(panel)` · `def_portfolio_equity(sim_panel)` · `def_max_drawdown(equity)` · `def_trade_stats(trade_ledger, equity)` · `def_buy_and_hold_stats(panel)` · `def_null_expectancies(base, panel, seed)` · `def_run_trade_backtest(base, membership)`
- **CLI**:`--out-dir` `--run-tag`
- **自測**:主程式可跑

### GRP_ENG015_SectorWhaleEngine
- **族**:`functional modules/GroupIndex/engine/VIA_SectorWhaleEngine`(版本 1;現役 `VIA_SectorWhaleEngine_v020.py`)
- **功能**:VIA_SectorWhaleEngine_v020.py — 準確率改良 + 完整回測(準確率/波動性)
- **函式**(9):`gen_world(seed, n)` · `zscore(s, kind, w, mp, lag)` · `sector_flows(df)` · `anchor_asof(wkdf, sec, dates)` · `detect(flow_z, anchor, cfg)` · `fuzzy(t, k)` · `metrics(sig, truth_dir)` · `backtest(cfg)` · `main()`
- **自測**:主程式可跑

### GRP_ENG016_ThreeListGroupingDynamicValidationPipeline
- **族**:`functional modules/GroupIndex/engine/VIA_ThreeList_Grouping_DynamicValidationPipeline`(版本 1;現役 `VIA_ThreeList_Grouping_DynamicValidationPipeline_v0201.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **類**:PipelineConfig
- **函式**(12):`def_configure_cjk_font()` · `def_now()` · `def_sha256(path)` · `def_stable_seed(text)` · `def_write_csv(df, path)` · `def_write_json(obj, path)` · `def_safe_float(value)` · `def_parse_pct(value)` · `def_sanitize_filename(name, max_len)` · `def_html_table(df, max_rows)`
- **CLI**:`--no-activate` `--no-backtest` `--no-plots` `--out-dir` `--run-tag` `--source-a` `--source-b` `--source-c`
- **自測**:主程式可跑

### GRP_ENG017_Init
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/__init__`(版本 1;現役 `__init__.py`)
- **功能**:台股月營收動能引擎 (Taiwan Stock Monthly Revenue Engine).
- **自測**:匯入型

### GRP_ENG018_Analyze
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/analyze`(版本 1;現役 `analyze.py`)
- **功能**:analyze.py -- 三層動能分析引擎.
- **函式**(5):`compute_company_metrics(g, cfg)` · `classify_pattern(m, cfg)` · `momentum_score(m, cfg)` · `tier(m, cfg)` · `analyze(data, cfg)`
- **自測**:匯入型

### GRP_ENG019_Classify
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/classify`(版本 1;現役 `classify.py`)
- **功能**:classify.py -- 產業分類 + 原物料/週期股全市場分流.
- **函式**(1):`tag_cyclical(df, cyclical_industries)`
- **自測**:匯入型

### GRP_ENG020_Cli
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/cli`(版本 1;現役 `cli.py`)
- **功能**:cli.py -- 命令列進入點.
- **函式**(9):`load_cfg(path)` · `cmd_fetch(cfg)` · `cmd_analyze(cfg, data)` · `cmd_report(cfg, result, data)` · `cmd_run(cfg)` · `cmd_demo(cfg)` · `cmd_groups(cfg)` · `cmd_selftest(cfg)` · `main(argv)`
- **CLI**:`--config`
- **自測**:主程式可跑

### GRP_ENG021_Fetch
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/fetch`(版本 1;現役 `fetch.py`)
- **功能**:fetch.py -- 從 MOPS 公開資訊觀測站抓取全上市/上櫃月營收.
- **函式**(3):`month_iter(months_back, ref)` · `fetch_page(session, hosts, market, year, month)` · `fetch_all(cfg, ref)`
- **自測**:匯入型

### GRP_ENG022_Groups
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/groups`(版本 1;現役 `groups.py`)
- **功能**:groups.py -- 熱門族群分類層 (VIA 族群分類 v1.1 疊加).
- **函式**(6):`load_groups(path)` · `attach_groups(analysis, groups)` · `group_momentum(analysis, groups, cfg)` · `cyclical_sector_groups(analysis)` · `order_sector_table(gt)` · `group_members_detail(analysis, groups, grp)`
- **自測**:匯入型

### GRP_ENG023_Report
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/report`(版本 1;現役 `report.py`)
- **功能**:report.py -- 單頁 HTML 儀表板 (視覺鎖定: VIA 族群分類 v1.1 風格).
- **自測**:匯入型

### GRP_ENG024_Store
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/store`(版本 1;現役 `store.py`)
- **功能**:store.py -- 月營收累計增量資料庫 (parquet SSOT + duckdb 查詢層).
- **函式**(2):`upsert(df, cfg)` · `load(cfg, months_back)`
- **自測**:匯入型

### GRP_ENG025_Synth
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/synth`(版本 1;現役 `synth.py`)
- **功能**:synth.py -- 產生合成月營收資料, 供離線測試與 demo.
- **函式**(1):`make_synthetic(cfg, ref)`
- **自測**:匯入型

### GRP_ENG026_Tests
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/tests`(版本 1;現役 `tests.py`)
- **功能**:tests.py -- 內建自我測試 (python -m twrevenue.cli selftest).
- **函式**(9):`t_regex()` · `t_parser()` · `t_sectors()` · `t_groups_ssot()` · `t_store()` · `t_duckdb()` · `t_url()` · `t_formula()` · `run_all()`
- **自測**:匯入型

### GRP_ENG027_TestVIAChipWarRevenue
- **族**:`functional modules/GroupIndex/engine/test_VIA_ChipWar_Revenue`(版本 1;現役 `test_VIA_ChipWar_Revenue_v0100.py`)
- **功能**:籌碼戰四引擎 + 月營收引擎整合契約測試(離線、輕量;重收證由 Evidence 執行器負責)。
- **函式**(5):`test_chipwar_registry_free_only_and_files_exist()` · `test_sectorwhale_ssot_tickers_are_groupindex_common_stocks()` · `test_revenue_groups_csv_contract()` · `test_revenue_selftest_module_importable_offline()` · `test_evidence_summary_gate()`
- **自測**:匯入型 · **整合邊**:VIA_ChipWar_Console_v010, VIA_SectorWhaleEngine_v020

### GRP_ENG028_TestVIAETFConsoles
- **族**:`functional modules/GroupIndex/engine/test_VIA_ETF_Consoles`(版本 1;現役 `test_VIA_ETF_Consoles_v0100.py`)
- **功能**:ETF 雙主控台(ActiveStockETF / GlobalETFFlow)整合契約測試。
- **函式**(5):`test_active_stock_etf_selftest_green()` · `test_global_etf_flow_selftest_green()` · `test_evidence_ladder_never_emits_syn()` · `test_universe_disjoint_from_groupindex_common_stocks()` · `test_global_flow_truth_ladder_t3_never_writes_amounts()`
- **自測**:匯入型 · **整合邊**:VIA_ActiveStockETF, VIA_GlobalETFFlow

### GRP_ENG029_TestVIAGroupIndexEnvPreflight
- **族**:`functional modules/GroupIndex/engine/test_VIA_GroupIndex_EnvPreflight`(版本 1;現役 `test_VIA_GroupIndex_EnvPreflight_v0100.py`)
- **功能**:環境前哨檢查測試:分類邏輯 / 工具檢核 / 白名單缺口 / fail-closed 語意。
- **函式**(5):`test_detect_env_classification_contract()` · `test_required_tools_all_importable()` · `test_whitelist_gap_matches_envmanager_contract()` · `test_report_only_never_hard_fails_and_writes_report()` · `test_enforce_blocks_outside_via_env()`
- **自測**:匯入型 · **整合邊**:VIA_GroupIndex_EnvPreflight_v0100

### GRP_ENG030_TestVIAGroupIndexOneClick
- **族**:`functional modules/GroupIndex/engine/test_VIA_GroupIndex_OneClick`(版本 1;現役 `test_VIA_GroupIndex_OneClick_v0100.py`)
- **功能**:OneClick PS1 靜態結構驗證(沙盒無 pwsh:結構/契約檢查,runtime 於本機執行)。
- **函式**(7):`strip_ps_literals(text)` · `test_ps1_balanced_delimiters()` · `test_ps1_references_all_engines_and_tests()` · `test_ps1_gate_matrix_covers_four_runs()` · `test_ps1_fail_closed_and_governance()` · `test_ps1_sync_hash_smoke_segments_contract()` · `test_ps1_env_preflight_segment_contract()`
- **CLI**:`--enforce`
- **自測**:匯入型

### GRP_ENG031_TestVIALiveWireContractAdapter
- **族**:`functional modules/GroupIndex/engine/test_VIA_LiveWire_ContractAdapter`(版本 1;現役 `test_VIA_LiveWire_ContractAdapter_v0100.py`)
- **功能**:無說明(候補)
- **函式**(6):`test_ticker_regex_contract()` · `test_schema_neutralizer_variants()` · `test_fetcher_fail_closed_never_fabricates()` · `test_panel_contract_gatekeeper()` · `test_reconcile_three_strategies()` · `test_evidence_run_gate_and_v11_reconcile()`
- **自測**:匯入型

### GRP_ENG032_TestVIASectorFlowAdaptiveChainedIndex
- **族**:`functional modules/GroupIndex/engine/test_VIA_SectorFlow_AdaptiveChainedIndex`(版本 1;現役 `test_VIA_SectorFlow_AdaptiveChainedIndex_v0100.py`)
- **功能**:無說明(候補)
- **函式**(9):`test_membership_contract()` · `test_cleaning_quarantines_non_common_and_strips_daytrade()` · `test_chained_index_continuity_and_base()` · `test_dynamic_criteria_adapt_across_scenarios()` · `test_market_tide_residual_control()` · `test_final_run_gate_and_activation()` · `test_manifest_integrity()` · `test_no_prohibited_fixed_market_thresholds_in_executable_ast()` · `test_lookahead_free_review_replay()`
- **自測**:匯入型

### GRP_ENG033_TestVIASectorFlowDashboardBuilder
- **族**:`functional modules/GroupIndex/engine/test_VIA_SectorFlow_Dashboard_Builder`(版本 1;現役 `test_VIA_SectorFlow_Dashboard_Builder_v0100.py`)
- **功能**:無說明(候補)
- **函式**(2):`test_payload_contract()` · `test_dashboard_html_self_contained()`
- **自測**:匯入型

### GRP_ENG034_TestVIASectorFlowSignalTradeBacktest
- **族**:`functional modules/GroupIndex/engine/test_VIA_SectorFlow_SignalTradeBacktest`(版本 1;現役 `test_VIA_SectorFlow_SignalTradeBacktest_v0100.py`)
- **功能**:無說明(候補)
- **函式**(6):`test_run_gate_and_ledger()` · `test_expectancy_beats_null_in_structured_scenarios()` · `test_macro_gate_protects_in_tide_and_drain()` · `test_costs_are_applied_and_positions_bounded()` · `test_trade_ledger_consistency()` · `test_manifest_integrity()`
- **自測**:匯入型

### GRP_ENG035_TestVIAThreeListGroupingDynamicValidationPipeline
- **族**:`functional modules/GroupIndex/engine/test_VIA_ThreeList_Grouping_DynamicValidationPipeline`(版本 1;現役 `test_VIA_ThreeList_Grouping_DynamicValidationPipeline_v0200.py`)
- **功能**:無說明(候補)
- **函式**(8):`locate_run_dir()` · `test_source_extraction_contracts()` · `test_counting_governance()` · `test_dynamic_criteria_adapt_across_regimes()` · `test_final_run_outputs_and_activation()` · `test_manifest_and_html_assets()` · `test_backtest_has_all_scenarios_and_dynamic_digests()` · `test_no_prohibited_fixed_market_thresholds_in_executable_ast()`
- **自測**:匯入型

### GRP_ENG036_TestVIAVAPAxisLock
- **族**:`functional modules/GroupIndex/engine/test_VIA_VAP_AxisLock`(版本 1;現役 `test_VIA_VAP_AxisLock_v0100.py`)
- **功能**:無說明(候補)
- **函式**(4):`test_vap_ticks_axis_contract_properties()` · `test_vap_spec_csv_archived()` · `test_vap_compliance_evidence()` · `test_dashboard_embeds_vap_block()`
- **自測**:匯入型

### GRP_ENG037_TestViaSubgroupSandboxValidation
- **族**:`functional modules/GroupIndex/engine/test_via_subgroup_sandbox_validation`(版本 1;現役 `test_via_subgroup_sandbox_validation_v0100.py`)
- **功能**:無說明(候補)
- **函式**(8):`def_sha256(path)` · `test_engine_v0201_compiles_on_this_python()` · `test_no_prohibited_fixed_market_thresholds_in_v0201_ast()` · `test_sandbox_run_summary_gate()` · `test_sandbox_test_ledger_no_hard_failures()` · `test_counting_governance_in_membership_input()` · `test_dynamic_criteria_adapt_and_no_fixed_thresholds()` · `test_evidence_manifest_verifies()`
- **自測**:匯入型

### GRP_ENG038_SubgroupSandboxValidation
- **族**:`functional modules/GroupIndex/engine/via_subgroup_sandbox_validation`(版本 1;現役 `via_subgroup_sandbox_validation_v0100.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **函式**(5):`load_engine()` · `def_extract_subgroup_ssot(path)` · `def_empty_dynamic(engine)` · `def_audit_fixed_thresholds(engine_path)` · `main(argv)`
- **CLI**:`--no-plots` `--out-dir` `--ssot`
- **自測**:主程式可跑


## PLG · 插件(18 支)

### PLG_ENG001_SuperExtract
- **族**:`functional modules/SuperDocExtractor/super_extract`(版本 1;現役 `super_extract.py`)
- **功能**:Entry point:  python super_extract.py <command> ...
- **自測**:主程式可跑 · **整合邊**:superextract

### PLG_ENG002_Init
- **族**:`functional modules/SuperDocExtractor/superextract/__init__`(版本 1;現役 `__init__.py`)
- **功能**:superextract — Word/Excel/CSV text & table extractor with encoding
- **自測**:匯入型

### PLG_ENG003_Main
- **族**:`functional modules/SuperDocExtractor/superextract/__main__`(版本 1;現役 `__main__.py`)
- **功能**:Allow `python -m superextract ...`.
- **自測**:主程式可跑

### PLG_ENG004_Availability
- **族**:`functional modules/SuperDocExtractor/superextract/availability`(版本 1;現役 `availability.py`)
- **功能**:Optional-dependency registry.
- **函式**(4):`has(name)` · `load(name)` · `doctor()` · `doctor_text()`
- **自測**:匯入型

### PLG_ENG005_Cli
- **族**:`functional modules/SuperDocExtractor/superextract/cli`(版本 1;現役 `cli.py`)
- **功能**:Command-line interface.
- **函式**(8):`cmd_doctor(_args)` · `cmd_extract(args)` · `cmd_validate(args)` · `cmd_compare(args)` · `cmd_crosscheck(args)` · `cmd_selftest(args)` · `build_parser()` · `main(argv)`
- **CLI**:`--delimiter` `--drop-layout-tables` `--encoding` `--engine` `--html` `--json` `--keep` `--key` `--no-datacompy` `--no-repair` `--outdir` `--output-encoding`
- **自測**:主程式可跑

### PLG_ENG006_Compare
- **族**:`functional modules/SuperDocExtractor/superextract/compare`(版本 1;現役 `compare.py`)
- **功能**:Comparison (對照): text diff, table pairing, cell-level diff.
- **類**:TextDiff, CellChange, TableDiff
- **函式**(7):`compare_texts(old, new, label_old, label_new, normalize)` · `html_side_by_side(old, new, label_old, label_new)` · `pair_tables(old_tables, new_tables, threshold)` · `cells_equal(a, b)` · `detect_key_column(g1, g2)` · `compare_grids(g_old, g_new, key, auto_key, with_datacompy)` · `crosscheck_docx(path)`
- **CLI**:`---`
- **自測**:匯入型

### PLG_ENG007_CsvExtract
- **族**:`functional modules/SuperDocExtractor/superextract/csv_extract`(版本 1;現役 `csv_extract.py`)
- **功能**:CSV extraction with encoding detection, dialect sniffing and ragged-row
- **類**:CsvResult
- **函式**(2):`sniff_dialect(sample)` · `extract_csv(path, encoding, delimiter, row_policy)`
- **自測**:匯入型

### PLG_ENG008_Encoding
- **族**:`functional modules/SuperDocExtractor/superextract/encoding`(版本 1;現役 `encoding.py`)
- **功能**:Encoding detection and byte decoding (編碼問題核心).
- **類**:DetectionResult
- **函式**(4):`sniff_bom(data)` · `detect_encoding(data)` · `decode_bytes(data, encoding)` · `read_text_auto(path, encoding)`
- **自測**:匯入型

### PLG_ENG009_ExcelExtract
- **族**:`functional modules/SuperDocExtractor/superextract/excel_extract`(版本 1;現役 `excel_extract.py`)
- **功能**:Excel (.xlsx / .xls) extraction into Grids.
- **類**:ExcelWorkbook
- **函式**(5):`col_to_index(ref)` · `split_ref(ref)` · `serial_to_datetime(serial, date1904)` · `extract_xlsx_rawxml(path, password, values)` · `extract_xlsx_openpyxl(path, password, values)`
- **自測**:匯入型

### PLG_ENG010_Pipeline
- **族**:`functional modules/SuperDocExtractor/superextract/pipeline`(版本 1;現役 `pipeline.py`)
- **功能**:High-level pipeline: extract -> repair -> validate -> report, for any of
- **類**:ExtractionResult
- **函式**(3):`detect_format(path)` · `extract_any(path, engine, encoding, password, values)` · `compare_files(old_path, new_path, key, with_datacompy, max_diff_lines)`
- **自測**:匯入型

### PLG_ENG011_Report
- **族**:`functional modules/SuperDocExtractor/superextract/report`(版本 1;現役 `report.py`)
- **功能**:Report rendering: one markdown/JSON view over extraction + repair +
- **函式**(5):`write_json(payload, path)` · `render_extraction_md(report)` · `render_comparison_md(report)` · `render_crosscheck_md(report)` · `dump_debug_json(payload)`
- **自測**:匯入型

### PLG_ENG012_Samples
- **族**:`functional modules/SuperDocExtractor/superextract/samples`(版本 1;現役 `samples.py`)
- **功能**:Sample-file factory for the selftest.
- **函式**(4):`write_docx(path, body_xml, with_header)` · `write_xlsx(path)` · `write_csvs(outdir)` · `build_all(outdir)`
- **自測**:匯入型

### PLG_ENG013_Selftest
- **族**:`functional modules/SuperDocExtractor/superextract/selftest`(版本 1;現役 `selftest.py`)
- **功能**:End-to-end selftest: generate pathological samples, run the full
- **函式**(12):`check_docx_text_and_track_changes(paths)` · `check_docx_invisible_char_repair(paths)` · `check_docx_merges(paths)` · `check_docx_nested_and_layout(paths)` · `check_docx_crosscheck(paths)` · `check_xlsx_both_engines(paths)` · `check_xlsx_validation(paths)` · `check_csv_big5(paths)` · `check_csv_bom(paths)` · `check_csv_mojibake(paths)`
- **自測**:匯入型

### PLG_ENG014_Tableops
- **族**:`functional modules/SuperDocExtractor/superextract/tableops`(版本 1;現役 `tableops.py`)
- **功能**:Grid: the common table structure every extractor produces.
- **類**:Grid
- **函式**(2):`dedupe_headers(names)` · `coerce_number(value)`
- **CLI**:`---`
- **自測**:匯入型

### PLG_ENG015_Textclean
- **族**:`functional modules/SuperDocExtractor/superextract/textclean`(版本 1;現役 `textclean.py`)
- **功能**:Text repair (修復): mojibake, invisible characters, normalization.
- **類**:CleanResult
- **函式**(5):`mojibake_score(text)` · `fix_mojibake(text)` · `clean_text(text, fix_encoding, normalize, strip_zero_width, strip_control)` · `normalize_for_compare(value)` · `find_invisible_chars(text)`
- **自測**:匯入型

### PLG_ENG016_Validate
- **族**:`functional modules/SuperDocExtractor/superextract/validate`(版本 1;現役 `validate.py`)
- **功能**:Validation (驗證): structural and content checks on extracted data.
- **類**:Issue
- **函式**(3):`validate_text(text, location)` · `validate_grid(grid, header_row)` · `summarize_issues(issues)`
- **自測**:匯入型

### PLG_ENG017_WordExtract
- **族**:`functional modules/SuperDocExtractor/superextract/word_extract`(版本 1;現役 `word_extract.py`)
- **功能**:Word (.docx) text + table extraction.
- **類**:ExtractionError, WordDocument
- **函式**(6):`sniff_container(path_or_bytes)` · `open_office_zip(path, password)` · `extract_docx_rawxml(path, password, include_headers_footers)` · `extract_docx_python_docx(path)` · `extract_docx_docx2python(path)` · `extract_docx(path, engine, password, include_headers_footers)`
- **CLI**:`----media/.*?----`
- **自測**:匯入型

### PLG_ENG018_TestExtractor
- **族**:`functional modules/SuperDocExtractor/tests/test_extractor`(版本 1;現役 `test_extractor.py`)
- **功能**:pytest wrapper around the selftest checks.
- **函式**(2):`sample_paths(tmp_path_factory)` · `test_pipeline(check, sample_paths)`
- **自測**:匯入型 · **整合邊**:superextract


## VAP · 視覺分析(3 支)

### VAP_ENG001_AutoplotEngineChartlib
- **族**:`functional modules/VAP/engine/via_autoplot_engine_chartlib`(版本 6;現役 `via_autoplot_engine_chartlib_v007.py`)
- **功能**:VIA · VeritasAutoPlot (VAP) engine v001 · 雙軸互比繪圖引擎.
- **函式**(5):`log(message)` · `discover_db_files(base, extra)` · `write_demo_db(base)` · `load_tables(path)` · `parse_x(value)`
- **CLI**:`--auto` `--bands` `--bar-style` `--base` `--db` `--demo` `--left` `--left-form` `--list` `--max-charts` `--out` `--panels`
- **自測**:主程式可跑

### VAP_ENG002_AutoplotEngine
- **族**:`functional modules/VAP/engine/via_autoplot_engine`(版本 1;現役 `via_autoplot_engine_v001.py`)
- **功能**:VIA · VeritasAutoPlot (VAP) engine v001 · 雙軸互比繪圖引擎.
- **函式**(8):`log(message)` · `discover_db_files(base, extra)` · `write_demo_db(base)` · `load_tables(path)` · `parse_x(value)` · `parse_number(value)` · `numeric_columns(rows)` · `x_column(rows, preferred)`
- **CLI**:`--auto` `--base` `--db` `--demo` `--left` `--left-form` `--list` `--max-charts` `--out` `--right` `--right-form` `--table`
- **自測**:主程式可跑

### VAP_ENG003_AutoplotSeabornPlotly
- **族**:`functional modules/VAP/engine/via_autoplot_seaborn_plotly`(版本 1;現役 `via_autoplot_seaborn_plotly_v0100.py`)
- **功能**:VIA · VeritasAutoPlot seaborn+plotly 引擎 v0100 — VAP-CH-01…28 全譜雙後端實作.
- **類**:VAPError, VAPUnsupported, Spec, SeabornBackend, PlotlyBackend
- **函式**(10):`find_ssot_dir(override)` · `nice_step(raw, multiples)` · `ticks_for(lo, hi, spec, n_intervals, headroom)` · `decimals_of(step)` · `fmt_tick(value, step, thousands)` · `dual_ticks(l_lo, l_hi, r_lo, r_hi, spec)` · `thin_labels(labels, max_labels)` · `demo_data(chart_id)` · `hex_to_rgba(hex_color, alpha)` · `hex_to_mpl_rgba(hex_color, alpha)`
- **CLI**:`--backend` `--chart` `--data` `--file` `--group` `--limit` `--map` `--out` `--plotlyjs` `--scale` `--ssot` `--table`
- **自測**:主程式可跑


## VDF · 數據鍛造(42 支)

### VDF_ENG001_DataHubOrchestrator
- **族**:`functional modules/VDF/VDF_DataHub_Orchestrator`(版本 2;現役 `VDF_DataHub_Orchestrator_v0101.py`)
- **功能**:VDF_DataHub_Orchestrator_v0101 — NoStall 版(正本零觸碰;版本前進)
- **函式**(3):`load_canon()` · `supportive_via_subprocess(core_root, timeout_sec)` · `main()`
- **CLI**:`--core-root` `--data-root` `--import-worker` `--output` `--run-root` `--skip-supportive` `--supportive-timeout`
- **自測**:主程式可跑

### VDF_ENG002_MDL001TWEquityEngine
- **族**:`functional modules/VDF/VDF_MDL001_TWEquityEngine`(版本 1;現役 `VDF_MDL001_TWEquityEngine.py`)
- **功能**:================================================================================
- **類**:IntelligentDependencyChecker, IntelligentModuleImporter, IndexFileManager, EquityFileManager, RealIndexFetcher, RealEquityFetcher, SmartAutoDeployController, EnhancedStockProcessor
- **函式**(10):`to_twse_yyyymmdd(dt)` · `to_twse_month(dt)` · `to_roc_slash(dt)` · `to_roc_dash(dt)` · `to_western_iso(dt)` · `get_date_range(s, e)` · `is_known_tw_holiday(dt)` · `safe_num(value)` · `print_raw_response(api_name, args, resp)` · `print_rich_summary_matrix(processor, deployment_success, processing_success)`
- **CLI**:`--equity-only` `--format=json` `--index-only` `--no-pause` `--only-reset` `--quiet` `--reset-all` `--reset-holidays` `--upgrade`
- **自測**:主程式可跑 · **整合邊**:VeritasAegisNexus, VeritasCeleritas

### VDF_ENG003_MDL001TWUniverseVerify
- **族**:`functional modules/VDF/VDF_MDL001_TWUniverseVerify`(版本 1;現役 `VDF_MDL001_TWUniverseVerify.py`)
- **功能**:================================================================================
- **類**:TWUniverseFetcher, TWUniverseVerifier, OutputManager
- **函式**(4):`apply_ssot_regex(code)` · `run_verify(dryrun)` · `print_summary_matrix(report, twse_pass, tpex_pass, combined_rej, mgr)` · `main()`
- **CLI**:`--dryrun` `--no-pause`
- **自測**:主程式可跑

### VDF_ENG004_MDL002YFinanceFetchingEngine
- **族**:`functional modules/VDF/VDF_MDL002_YFinanceFetchingEngine`(版本 1;現役 `VDF_MDL002_YFinanceFetchingEngine.py`)
- **功能**:================================================================================
- **類**:FileManager, DataValidator, ETFFundFlowCalculator, FinancialDataFetcher, YFinanceUniverseTool
- **函式**(9):`validate_ticker(ticker, market_group)` · `detect_tw_ticker_format(s)` · `check_and_install_dependencies()` · `print_rich_summary_matrix(tool, df_main, df_flow, df_composite)` · `main()` · `tool_run(tool)` · `interactive_menu()` · `view_existing_data()` · `cleanup_backups()`
- **CLI**:`--etf-only` `--menu` `--no-flows` `--no-pause` `--non-etf-only`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified

### VDF_ENG005_MDL003SentimentMacroEngine
- **族**:`functional modules/VDF/VDF_MDL003_SentimentMacroEngine`(版本 1;現役 `VDF_MDL003_SentimentMacroEngine.py`)
- **功能**:================================================================================
- **類**:AAIIFetcher, CNNFearGreedFetcher, FREDFetcher, AKShareFetcher, OutputManager, SentimentMacroEngine
- **函式**(3):`print_rich_summary_matrix(eng)` · `main()` · `interactive_menu()`
- **CLI**:`--aaii` `--akshare` `--cnn` `--fred` `--gsheet` `--menu` `--no-aaii` `--no-akshare` `--no-cnn` `--no-csv` `--no-duckdb` `--no-fred`
- **自測**:主程式可跑

### VDF_ENG006_MDL004TWFullMarketEngine
- **族**:`functional modules/VDF/VDF_MDL004_TWFullMarketEngine`(版本 1;現役 `VDF_MDL004_TWFullMarketEngine.py`)
- **功能**:================================================================================
- **類**:TWSEFullMarketFetcher, TPEXFullMarketFetcher, YFHistoryBulkFetcher, YFConsensusFetcher, FactSetConsensusFetcher, SMAVolMcapCalculator, TWFullMarketEngine
- **函式**(1):`main()`
- **CLI**:`--max` `--no-consensus` `--no-history` `--no-pause` `--universe-source`
- **自測**:主程式可跑

### VDF_ENG007_MDL005TWStockFilter
- **族**:`functional modules/VDF/VDF_MDL005_TWStockFilter`(版本 1;現役 `VDF_MDL005_TWStockFilter.py`)
- **功能**:================================================================================
- **類**:YFinanceConsensusFetcher, FactSetConsensusFetcher, UpsideCalculator, UniverseLoader, OutputManager, StockFilterEngine
- **函式**(2):`print_rich_summary(eng)` · `main()`
- **CLI**:`--gsheet` `--max` `--no-csv` `--no-duckdb` `--no-json` `--no-parquet` `--no-pause` `--tickers` `--universe`
- **自測**:主程式可跑

### VDF_ENG008_MDL006FinancialModel
- **族**:`functional modules/VDF/VDF_MDL006_FinancialModel`(版本 1;現役 `VDF_MDL006_FinancialModel.py`)
- **功能**:================================================================================
- **類**:YFinanceFinancialFetcher, RatioAnalyzer, ValuationAnalyzer, BandChartBuilder, OutputManager, FinancialModelEngine
- **函式**(2):`print_rich_summary(eng)` · `main()`
- **CLI**:`--json` `--max` `--no-charts` `--no-csv` `--no-duckdb` `--no-parquet` `--no-pause` `--period` `--tickers`
- **自測**:主程式可跑

### VDF_ENG009_MDL007SSOTResolver
- **族**:`functional modules/VDF/VDF_MDL007_SSOTResolver`(版本 1;現役 `VDF_MDL007_SSOTResolver.py`)
- **功能**:================================================================================
- **類**:TickerResolver, TWSESource, TPEXSource, MOPSSource, YFinanceSource, FactSetSource, SSOTResolverEngine
- **函式**(1):`main()`
- **CLI**:`--all` `--batch` `--name` `--no-consensus` `--no-pause` `--ticker`
- **自測**:主程式可跑

### VDF_ENG010_MDL101OutputManager
- **族**:`functional modules/VDF/VDF_MDL101_OutputManager`(版本 1;現役 `VDF_MDL101_OutputManager.py`)
- **功能**:================================================================================
- **類**:OutputManager
- **CLI**:`--gsheet` `--no-csv` `--no-duckdb` `--no-json` `--no-parquet`
- **自測**:主程式可跑

### VDF_ENG011_MDL102FormatUpgrader
- **族**:`functional modules/VDF/VDF_MDL102_FormatUpgrader`(版本 1;現役 `VDF_MDL102_FormatUpgrader.py`)
- **功能**:================================================================================
- **類**:FormatUpgrader
- **函式**(1):`main()`
- **CLI**:`--dryrun` `--modules` `--no-pause`
- **自測**:主程式可跑

### VDF_ENG012_MDL103MasterRegistry
- **族**:`functional modules/VDF/VDF_MDL103_MasterRegistry`(版本 1;現役 `VDF_MDL103_MasterRegistry.py`)
- **功能**:================================================================================
- **類**:MasterRegistryEngine
- **函式**(1):`main()`
- **CLI**:`--check` `--filter` `--no-pause`
- **自測**:主程式可跑

### VDF_ENG013_MDL104RegistryLoader
- **族**:`functional modules/VDF/VDF_MDL104_RegistryLoader`(版本 1;現役 `VDF_MDL104_RegistryLoader.py`)
- **功能**:================================================================================
- **類**:RegistryLoader
- **函式**(1):`main()`
- **CLI**:`--dry-run` `--filter` `--no-pause` `--registry` `--schema` `--themes`
- **自測**:主程式可跑

### VDF_ENG014_MDL105CrossValidator
- **族**:`functional modules/VDF/VDF_MDL105_CrossValidator`(版本 1;現役 `VDF_MDL105_CrossValidator.py`)
- **功能**:================================================================================
- **類**:CrossValidator
- **函式**(1):`main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest

### VDF_ENG015_MDL201GenerateFullRegistry
- **族**:`functional modules/VDF/VDF_MDL201_GenerateFullRegistry`(版本 1;現役 `VDF_MDL201_GenerateFullRegistry.py`)
- **功能**:================================================================================
- **函式**(9):`extract_fred_registry()` · `extract_akshare_registry()` · `extract_yf_universe()` · `build_fred_item(via_code, meta)` · `build_akshare_item(code, meta)` · `build_yf_item(ticker, name, group, rule)` · `build_sentiment_items()` · `build_tw_universe_dynamic()` · `main()`
- **CLI**:`--no-pause` `--validate`
- **自測**:主程式可跑

### VDF_ENG016_MDL301SystemTest
- **族**:`functional modules/VDF/VDF_MDL301_SystemTest`(版本 1;現役 `VDF_MDL301_SystemTest.py`)
- **功能**:================================================================================
- **函式**(6):`check_dependencies()` · `test_output_manager()` · `test_upgrader()` · `check_module_files()` · `print_grand_summary(deps, om_test, upg_test, files)` · `main()`
- **CLI**:`--modules` `--no-pause`
- **自測**:主程式可跑

### VDF_ENG017_MDL302FinalActivation
- **族**:`functional modules/VDF/VDF_MDL302_FinalActivation`(版本 1;現役 `VDF_MDL302_FinalActivation.py`)
- **功能**:================================================================================
- **函式**(9):`phase1_dependencies()` · `phase2_imports()` · `phase3_mock_data()` · `phase4_pipeline(mock_data, imports)` · `phase5_integrity(sandbox)` · `phase6_integration(sandbox)` · `phase7_edge_cases(imports)` · `print_grand_summary(deps, imports, mock_data, sandbox)` · `main()`
- **CLI**:`--modules` `--no-pause` `--quick` `--tickers`
- **自測**:主程式可跑

### VDF_ENG018_MDL303RegistryActivation
- **族**:`functional modules/VDF/VDF_MDL303_RegistryActivation`(版本 1;現役 `VDF_MDL303_RegistryActivation.py`)
- **功能**:================================================================================
- **函式**(6):`phase1_generator()` · `phase2_validation()` · `phase3_loader()` · `phase4_crossvalidator(loader)` · `print_grand_summary(registry)` · `main()`
- **CLI**:`--validate`
- **自測**:主程式可跑

### VDF_ENG019_MDL501FetchContractManager
- **族**:`functional modules/VDF/VDF_MDL501_FetchContractManager`(版本 1;現役 `VDF_MDL501_FetchContractManager.py`)
- **功能**:VDF 取數契約管理器 v0100(MDL501)— 擷取項目 增/減/查/比 一支到底
- **函式**(10):`load()` · `save(c, action)` · `index(c)` · `cmd_check()` · `cmd_list(dom, status)` · `cmd_diff(other)` · `cmd_add(dom, code, item, source, fetcher)` · `cmd_remove(code, note)` · `cmd_setstatus(code, status)` · `main(argv)`
- **自測**:主程式可跑

### VDF_ENG020_MDL097VrnFinancialdataFinalEvidenceSelectorV06149FINANCIALDATAV06149
- **族**:`functional modules/VDF/VRN_MDL097_vrn_financialdata_final_evidence_selector_v06149__FINANCIALDATA__v06149`(版本 1;現役 `VRN_MDL097_vrn_financialdata_final_evidence_selector_v06149__FINANCIALDATA__v06149.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_is_blank(x)` · `def_to_float(x)` · `def_fmt_num(x, digits)` · `def_fmt_pct(numer, denom)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(root, patterns)`
- **自測**:主程式可跑

### VDF_ENG021_MDL215VrnFinancialdataTriflowStagingV06153FINANCIALDATAV06153
- **族**:`functional modules/VDF/VRN_MDL215_vrn_financialdata_triflow_staging_v06153__FINANCIALDATA__v06153`(版本 1;現役 `VRN_MDL215_vrn_financialdata_triflow_staging_v06153__FINANCIALDATA__v06153.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_light(sev)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_find_latest_json(run_root, pattern)` · `def_flatten_json_rows(obj, source_name)` · `def_first(row, names)` · `def_pct(n, d)` · `def_input_manifest(input_dir)`
- **自測**:主程式可跑

### VDF_ENG022_MDL218VrnFinancialDataConfirmVerifyV06125FINANCIALDATAV06125
- **族**:`functional modules/VDF/VRN_MDL218_vrn_financial_data_confirm_verify_v06125__FINANCIALDATA__v06125`(版本 1;現役 `VRN_MDL218_vrn_financial_data_confirm_verify_v06125__FINANCIALDATA__v06125.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_status_lights(sev)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_read_csv_any(path)` · `def_import_module(path)` · `def_compile_import(path)` · `def_backup(path, tag)` · `def_replace_function(text, func_name, new_func)` · `def_patch_bridge_date_noise(bridge_path)`
- **自測**:主程式可跑

### VDF_ENG023_MDL252VrnFinancialFinalSealV06127FINANCIALDATAV06127
- **族**:`functional modules/VDF/VRN_MDL252_vrn_financial_final_seal_v06127__FINANCIALDATA__v06127`(版本 1;現役 `VRN_MDL252_vrn_financial_final_seal_v06127__FINANCIALDATA__v06127.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_first(row, keys)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(run_root, pattern)` · `def_apply_final_alias(row)` · `def_is_db_ready(row)`
- **自測**:主程式可跑

### VDF_ENG024_MDL253VrnFinancialFinalSealV06127FINANCIALDATAV06127
- **族**:`functional modules/VDF/VRN_MDL253_vrn_financial_final_seal_v06127__FINANCIALDATA__v06127`(版本 1;現役 `VRN_MDL253_vrn_financial_final_seal_v06127__FINANCIALDATA__v06127.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_first(row, keys)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(run_root, pattern)` · `def_apply_final_alias(row)` · `def_is_db_ready(row)`
- **自測**:主程式可跑

### VDF_ENG025_MDL001TWUniverseVerify
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL001_TWUniverseVerify`(版本 1;現役 `VDF_MDL001_TWUniverseVerify_v0100R.py`)
- **功能**:================================================================================
- **類**:TWUniverseFetcher, TWUniverseVerifyEngine
- **CLI**:`--no-pause`
- **自測**:主程式可跑

### VDF_ENG026_MDL003SentimentMacroEngine
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL003_SentimentMacroEngine`(版本 1;現役 `VDF_MDL003_SentimentMacroEngine_v0100R.py`)
- **功能**:================================================================================
- **類**:AAIIFetcher, CNNFearGreedFetcher, FREDFetcher, AKShareFetcher, SentimentMacroEngine
- **CLI**:`--no-pause`
- **自測**:主程式可跑

### VDF_ENG027_MDL005TWStockFilter
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL005_TWStockFilter`(版本 1;現役 `VDF_MDL005_TWStockFilter_v0100R.py`)
- **功能**:================================================================================
- **類**:StockFilterEngine
- **CLI**:`--no-pause` `--tickers`
- **自測**:主程式可跑

### VDF_ENG028_MDL006FinancialModel
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL006_FinancialModel`(版本 1;現役 `VDF_MDL006_FinancialModel_v0100R.py`)
- **功能**:================================================================================
- **類**:FinancialModelEngine
- **CLI**:`--no-pause` `--tickers`
- **自測**:主程式可跑

### VDF_ENG029_MDL101OutputManager
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL101_OutputManager`(版本 1;現役 `VDF_MDL101_OutputManager_v0100R.py`)
- **功能**:================================================================================
- **類**:OutputManager
- **CLI**:`--no-%s`
- **自測**:主程式可跑

### VDF_ENG030_MDL103MasterRegistry
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL103_MasterRegistry`(版本 1;現役 `VDF_MDL103_MasterRegistry_v0100R.py`)
- **功能**:================================================================================
- **類**:MasterRegistryEngine
- **CLI**:`--no-pause`
- **自測**:主程式可跑

### VDF_ENG031_MDL001TWUniverseVerify
- **族**:`functional modules/VDF/engine/VDF_MDL001_TWUniverse_Verify`(版本 1;現役 `VDF_MDL001_TWUniverse_Verify.py`)
- **功能**:================================================================================
- **類**:TWUniverseFetcher, TWUniverseVerifier, OutputManager
- **函式**(4):`apply_ssot_regex(code)` · `run_verify(dryrun)` · `print_summary_matrix(report, twse_pass, tpex_pass, combined_rej, mgr)` · `main()`
- **CLI**:`--dryrun` `--no-pause`
- **自測**:主程式可跑

### VDF_ENG032_MDL002YFinanceFetchingEngine
- **族**:`functional modules/VDF/engine/VDF_MDL002_YFinanceFetchingEngine`(版本 1;現役 `VDF_MDL002_YFinanceFetchingEngine.py`)
- **功能**:================================================================================
- **類**:FileManager, DataValidator, ETFFundFlowCalculator, FinancialDataFetcher, YFinanceUniverseTool
- **函式**(9):`validate_ticker(ticker, market_group)` · `detect_tw_ticker_format(s)` · `check_and_install_dependencies()` · `print_rich_summary_matrix(tool, df_main, df_flow, df_composite)` · `main()` · `tool_run(tool)` · `interactive_menu()` · `view_existing_data()` · `cleanup_backups()`
- **CLI**:`--etf-only` `--menu` `--no-flows` `--no-pause` `--non-etf-only`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified

### VDF_ENG033_MDL003SentimentMacroEngine
- **族**:`functional modules/VDF/engine/VDF_MDL003_SentimentMacroEngine`(版本 1;現役 `VDF_MDL003_SentimentMacroEngine.py`)
- **功能**:================================================================================
- **類**:AAIIFetcher, CNNFearGreedFetcher, FREDFetcher, AKShareFetcher, OutputManager, SentimentMacroEngine
- **函式**(3):`print_rich_summary_matrix(eng)` · `main()` · `interactive_menu()`
- **CLI**:`--aaii` `--akshare` `--cnn` `--fred` `--gsheet` `--menu` `--no-aaii` `--no-akshare` `--no-cnn` `--no-csv` `--no-duckdb` `--no-fred`
- **自測**:主程式可跑

### VDF_ENG034_MDL005TWStockFilter
- **族**:`functional modules/VDF/engine/VDF_MDL005_TWStockFilter`(版本 1;現役 `VDF_MDL005_TWStockFilter.py`)
- **功能**:================================================================================
- **類**:YFinanceConsensusFetcher, FactSetConsensusFetcher, UpsideCalculator, UniverseLoader, OutputManager, StockFilterEngine
- **函式**(2):`print_rich_summary(eng)` · `main()`
- **CLI**:`--gsheet` `--max` `--no-csv` `--no-duckdb` `--no-json` `--no-parquet` `--no-pause` `--tickers` `--universe`
- **自測**:主程式可跑

### VDF_ENG035_MDL006FinancialModel
- **族**:`functional modules/VDF/engine/VDF_MDL006_FinancialModel`(版本 1;現役 `VDF_MDL006_FinancialModel.py`)
- **功能**:================================================================================
- **類**:YFinanceFinancialFetcher, RatioAnalyzer, ValuationAnalyzer, BandChartBuilder, OutputManager, FinancialModelEngine
- **函式**(2):`print_rich_summary(eng)` · `main()`
- **CLI**:`--json` `--max` `--no-charts` `--no-csv` `--no-duckdb` `--no-parquet` `--no-pause` `--period` `--tickers`
- **自測**:主程式可跑

### VDF_ENG036_MDL007SSOTResolver
- **族**:`functional modules/VDF/engine/VDF_MDL007_SSOTResolver`(版本 1;現役 `VDF_MDL007_SSOTResolver.py`)
- **功能**:================================================================================
- **類**:TickerResolver, TWSESource, TPEXSource, MOPSSource, YFinanceSource, FactSetSource, SSOTResolverEngine
- **函式**(1):`main()`
- **CLI**:`--all` `--batch` `--name` `--no-consensus` `--no-pause` `--ticker`
- **自測**:主程式可跑

### VDF_ENG037_MDL103MasterRegistry
- **族**:`functional modules/VDF/engine/VDF_MDL103_MasterRegistry`(版本 1;現役 `VDF_MDL103_MasterRegistry.py`)
- **功能**:================================================================================
- **類**:MasterRegistryEngine
- **函式**(1):`main()`
- **CLI**:`--check` `--filter` `--no-pause`
- **自測**:主程式可跑

### VDF_ENG038_MDL301SystemTest
- **族**:`functional modules/VDF/engine/VDF_MDL301_SystemTest`(版本 1;現役 `VDF_MDL301_SystemTest.py`)
- **功能**:================================================================================
- **函式**(6):`check_dependencies()` · `test_output_manager()` · `test_upgrader()` · `check_module_files()` · `print_grand_summary(deps, om_test, upg_test, files)` · `main()`
- **CLI**:`--modules` `--no-pause`
- **自測**:主程式可跑

### VDF_ENG039_Inject
- **族**:`functional modules/VDF/engine/VIA_Inject`(版本 1;現役 `VIA_Inject.py`)
- **功能**:VIA_Inject — 第5步：把 VIA_VDF_Bridge 標準輸出 → 兩模板各自的資料結構並注入 HTML
- **函式**(5):`build_equity(real)` · `build_etf(real)` · `inject_html(path, var_js, marker_id)` · `offline_demo_real()` · `main()`
- **CLI**:`--inject-equity` `--inject-etf` `--offline-demo` `--out-dir` `--real`
- **自測**:主程式可跑

### VDF_ENG040_TWUniverseBuilder
- **族**:`functional modules/VDF/engine/VIA_TW_Universe_Builder`(版本 1;現役 `VIA_TW_Universe_Builder.py`)
- **功能**:VIA_TW_Universe_Builder — 第一階段：建出「全台股」基礎宇宙(TWSE+TPEx)
- **函式**(6):`probe()` · `fetch_twse(requests)` · `fetch_tpex(requests)` · `offline_demo()` · `write_outputs(rows, out_json, duckdb_path)` · `main()`
- **CLI**:`--duckdb` `--offline-demo` `--out` `--probe-urls`
- **自測**:主程式可跑

### VDF_ENG041_SectorRotationCapitalFlowEngine
- **族**:`functional modules/VDF/engine/candidates/sector_rotation_capital_flow_engine`(版本 1;現役 `sector_rotation_capital_flow_engine.py`)
- **功能**:無說明(候補)
- **類**:SectorRotationEngine
- **函式**(1):`generate_noisy_market_data(days)`
- **自測**:主程式可跑

### VDF_ENG042_MoviesIntake
- **族**:`functional modules/VDF/engine/vdf_movies_intake`(版本 1;現役 `vdf_movies_intake_v001.py`)
- **功能**:VIA · VeritasDataForge (VDF) movies intake v001 · 電影資料集鍛造引擎.
- **函式**(11):`log(message)` · `sha256_file(path)` · `read_csv(path)` · `to_float(raw)` · `to_year(raw)` · `mean(values)` · `build_genres_summary(rows)` · `build_yearly_box_office(rows)` · `build_yearly_tmdb(rows)` · `forge(base, source_dir, mode)`
- **CLI**:`--base` `--mode` `--source`
- **自測**:主程式可跑


## VIA · 泛功能(147 支)

### VIA_ENG001_MultiFactorTestValidateSimEngine
- **族**:`functional modules/MultiFactor/engines/VIA_MultiFactor_TestValidateSim_Engine`(版本 1;現役 `VIA_MultiFactor_TestValidateSim_Engine_v0100.py`)
- **功能**:VIA MultiFactor Test / Validate / Simulate Engine v0.1.00
- **類**:GovernancePolicy, FactorResult, AntiValidationResult, SimulationRow
- **函式**(12):`html_escape(x)` · `ensure_append_only_run_dir(out_base, run_id)` · `load_governance_policy(ssot_path)` · `safe_float(x, default)` · `ols_r2_beta(y, x)` · `generate_demo_panel(n, seed)` · `load_panel(args)` · `numeric_factor_columns(df, target)` · `auto_candidate_windows(n)` · `align_lagged(factor, target, lag)`
- **CLI**:`--date-col` `--demo-rows` `--input-panel` `--out-base` `--run-id` `--seed` `--ssot` `--target`
- **自測**:主程式可跑

### VIA_ENG002_TestVIAMultiFactorTestValidateSimEngine
- **族**:`functional modules/MultiFactor/engines/test_VIA_MultiFactor_TestValidateSim_Engine`(版本 2;現役 `test_VIA_MultiFactor_TestValidateSim_Engine_v0101.py`)
- **功能**:無說明(候補)
- **函式**(3):`test_demo_panel_shape()` · `test_engine_run_outputs()` · `test_projection_not_confirmed_in_outputs()`
- **CLI**:`--demo-rows` `--out-base` `--seed`
- **自測**:主程式可跑

### VIA_ENG003_TALibEngine
- **族**:`functional modules/TALib/VIA_TALibEngine`(版本 1;現役 `VIA_TALibEngine.py`)
- **功能**:VIA_TALibEngine.py v0100 — TA-Lib 技術指標引擎(原生 numpy 實作 + talib 在位直用)
- **類**:TAError
- **函式**(8):`load_price_rules()` · `load_table(path, table)` · `load_ohlcv(path, table, price_rules)` · `sma(x, n)` · `ema(x, n)` · `dema(x, n)` · `tema(x, n)` · `kama(x, n)`
- **CLI**:`--backend` `--category` `--file` `--indicators` `--json` `--map` `--out` `--period` `--table`
- **自測**:主程式可跑

### VIA_ENG004_VmtAiTriage
- **族**:`functional modules/VMT/engines/vmt_ai_triage`(版本 1;現役 `vmt_ai_triage.py`)
- **功能**:============================================================================
- **函式**(4):`triage_one(mail, llm, base_date)` · `run(ws, commit, use_llm, no_open, base_date)` · `load_triage(ws)` · `main()`
- **CLI**:`--llm`
- **自測**:主程式可跑

### VIA_ENG005_VmtCore
- **族**:`functional modules/VMT/engines/vmt_core`(版本 1;現役 `vmt_core.py`)
- **功能**:============================================================================
- **類**:Workspace, Ledger, EventLog, Quarantine, LocalLLM, EngineResult
- **函式**(11):`now_iso()` · `today()` · `md5_bytes(b)` · `fingerprint()` · `norm_case(s)` · `clip(s, n)` · `banner(title, subtitle)` · `mode_label(commit)` · `read_jsonl(path)` · `append_jsonl(path, rec, durable)`
- **CLI**:`--commit` `--no-open` `--root`
- **自測**:匯入型

### VIA_ENG006_VmtDashboard
- **族**:`functional modules/VMT/engines/vmt_dashboard`(版本 1;現役 `vmt_dashboard.py`)
- **功能**:============================================================================
- **函式**(2):`run(ws, commit, no_open, as_of)` · `main()`
- **CLI**:`--as-of`
- **自測**:主程式可跑

### VIA_ENG007_VmtExtractTasks
- **族**:`functional modules/VMT/engines/vmt_extract_tasks`(版本 1;現役 `vmt_extract_tasks.py`)
- **功能**:============================================================================
- **函式**(5):`from_mails(ws, me)` · `from_minutes(ws, include_questions)` · `find_duplicates(candidates, existing)` · `run(ws, me, commit, no_open, include_questions)` · `main()`
- **CLI**:`--include-questions` `--me`
- **自測**:主程式可跑

### VIA_ENG008_VmtLang
- **族**:`functional modules/VMT/engines/vmt_lang`(版本 1;現役 `vmt_lang.py`)
- **功能**:============================================================================
- **函式**(7):`split_sentences(text, max_len)` · `zh2int(s)` · `resolve_due(text, base)` · `classify_mail(subject, body, has_checkbox_reply)` · `classify_sentence(text, is_chair, base_date)` · `strip_fillers(text)` · `to_traditional(text, config)`
- **自測**:匯入型

### VIA_ENG009_VmtMailComposer
- **族**:`functional modules/VMT/engines/vmt_mail_composer`(版本 1;現役 `vmt_mail_composer.py`)
- **功能**:============================================================================
- **函式**(3):`compose(reminder, sender_name, as_of, roster)` · `run(ws, commit, no_open, draft, send)` · `main()`
- **CLI**:`--as-of` `--draft` `--me` `--send` `--sender`
- **自測**:主程式可跑

### VIA_ENG010_VmtMeetingMinutes
- **族**:`functional modules/VMT/engines/vmt_meeting_minutes`(版本 1;現役 `vmt_meeting_minutes.py`)
- **功能**:============================================================================
- **函式**(8):`load_transcript(src)` · `segment(segs, speaker_map, max_len)` · `flag_hallucinations(utts, no_speech_max)` · `clean(utts, vocab, traditional)` · `resolve_subjects(utts, roster)` · `tag_utterances(utts, chair, base_date)` · `agenda_hits(text, agenda, threshold)` · `split_topics(utts, agenda, chair, gap)`
- **CLI**:`---` `--config` `--transcript`
- **自測**:主程式可跑

### VIA_ENG011_VmtOutlookIntake
- **族**:`functional modules/VMT/engines/vmt_outlook_intake`(版本 1;現役 `vmt_outlook_intake.py`)
- **功能**:============================================================================
- **函式**(8):`thread_key(subject, case)` · `normalize_mail(raw, source)` · `source_outlook(days_back)` · `source_folder(inbox)` · `source_sample()` · `run(ws, source, days_back, commit, no_open)` · `load_mails(ws)` · `main()`
- **CLI**:`--days-back` `--source`
- **自測**:主程式可跑

### VIA_ENG012_VmtPipeline
- **族**:`functional modules/VMT/engines/vmt_pipeline`(版本 1;現役 `vmt_pipeline.py`)
- **功能**:============================================================================
- **函式**(2):`run(ws, commit, no_open, transcript, meeting_config)` · `main()`
- **CLI**:`--as-of` `--commit` `--demo` `--draft` `--llm` `--me` `--meeting-config` `--no-open` `--root` `--send` `--source` `--transcript`
- **自測**:主程式可跑

### VIA_ENG013_VmtProjects
- **族**:`functional modules/VMT/engines/vmt_projects`(版本 1;現役 `vmt_projects.py`)
- **功能**:============================================================================
- **函式**(7):`parse_code(text)` · `strip_code(name)` · `load_projects(ws)` · `resolve_project(text, ws)` · `scan(ws)` · `run(ws, commit, no_open)` · `main()`
- **自測**:主程式可跑

### VIA_ENG014_VmtReplyParser
- **族**:`functional modules/VMT/engines/vmt_reply_parser`(版本 1;現役 `vmt_reply_parser.py`)
- **功能**:============================================================================
- **函式**(3):`parse_reply(mail, base_date)` · `run(ws, commit, no_open, base_date)` · `main()`
- **自測**:主程式可跑

### VIA_ENG015_VmtSlaEngine
- **族**:`functional modules/VMT/engines/vmt_sla_engine`(版本 1;現役 `vmt_sla_engine.py`)
- **功能**:============================================================================
- **函式**(4):`sla_table(ws)` · `plan(ws, as_of)` · `run(ws, commit, no_open, as_of)` · `main()`
- **CLI**:`--as-of`
- **自測**:主程式可跑

### VIA_ENG016_VmtTaskSsot
- **族**:`functional modules/VMT/engines/vmt_task_ssot`(版本 1;現役 `vmt_task_ssot.py`)
- **功能**:============================================================================
- **函式**(8):`task_fingerprint(source_type, ref, cite, title)` · `build_task(title, owner, due, urgency, source_type)` · `create_tasks(ws, candidates, commit)` · `load_tasks(ws)` · `derive_states(ws, events, as_of)` · `open_tasks(ws, as_of)` · `run(ws, commit, no_open, as_of)` · `main()`
- **自測**:主程式可跑

### VIA_ENG017_TestVmtEngines
- **族**:`functional modules/VMT/tests/test_vmt_engines`(版本 1;現役 `test_vmt_engines.py`)
- **功能**:VMT 引擎測試 — 標準庫 unittest, 無外部相依。
- **類**:TempWS, TestLang, TestMinutes, TestClosedLoop, TestGovernance, TestDurability, TestProjects
- **自測**:主程式可跑

### VIA_ENG018_DuckParquetAcceptance
- **族**:`functional modules/WorkOps/MeetingLoop/via_duck_parquet_acceptance`(版本 1;現役 `via_duck_parquet_acceptance.py`)
- **功能**:無說明(候補)
- **函式**(9):`def_now_iso()` · `def_version(name)` · `def_sha256(path)` · `def_write_json(path, payload)` · `def_read_csv(path)` · `def_normalize_action_rows(rows)` · `def_run_real_engine()` · `def_run_acceptance()` · `def_main()`
- **CLI**:`--source` `--strict`
- **自測**:主程式可跑

### VIA_ENG019_MeetingloopEngine
- **族**:`functional modules/WorkOps/MeetingLoop/via_meetingloop_engine`(版本 1;現役 `via_meetingloop_engine.py`)
- **功能**:無說明(候補)
- **類**:Segment, Action
- **函式**(12):`def_now()` · `def_now_iso()` · `def_load_json(path, default)` · `def_write_json(path, data)` · `def_write_text(path, text)` · `def_read_text(path)` · `def_sha256_bytes(data)` · `def_sha256_text(text)` · `def_ensure_dirs()` · `def_make_run_dir(meeting_id)`
- **CLI**:`--meeting-id` `--review` `--source`
- **自測**:主程式可跑

### VIA_ENG020_SuperBOMContentParser
- **族**:`functional modules/WorkOps/VMT/VIA_SuperBOM_ContentParser`(版本 1;現役 `VIA_SuperBOM_ContentParser_v0100.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now_iso()` · `def_run_id()` · `def_safe_str(value)` · `def_sha12(text)` · `def_to_float(value)` · `def_split_refdes(value)` · `def_read_csv(path)` · `def_read_json_records(path)` · `def_norm_header(name)` · `def_map_headers(headers)`
- **CLI**:`--bom` `--db` `--from-proposals` `--output-root` `--selftest` `--top`
- **自測**:✅ --selftest

### VIA_ENG021_MasterEngine
- **族**:`functional modules/WorkOps/VMT/via_master_engine`(版本 4;現役 `via_master_engine_v0103.py`)
- **功能**:============================================================================
- **函式**(7):`hsafe(s)` · `load_params()` · `P(cfg, default)` · `wire_overrides(cfg, root, log)` · `run_stage(cfg, root, st, log)` · `build_report(cfg, root, log, out_html)` · `main()`
- **CLI**:`--no-open`
- **自測**:主程式可跑

### VIA_ENG022_VmtConvergence
- **族**:`functional modules/WorkOps/VMT/vmt_convergence`(版本 1;現役 `vmt_convergence.py`)
- **功能**:============================================================================
- **函式**(12):`hsafe(s)` · `now()` · `parse_dt(s)` · `load_params()` · `P(cfg, default)` · `load_issues(root, cfg)` · `ingest_confirmations(root, cfg)` · `build_rows(items, cfg)` · `try_sklearn(rows, labels, cfg)` · `rule_fallback(rows, labels, cfg)`
- **自測**:主程式可跑

### VIA_ENG023_VmtPlanningCpm
- **族**:`functional modules/WorkOps/VMT/vmt_planning_cpm`(版本 1;現役 `vmt_planning_cpm.py`)
- **功能**:============================================================================
- **函式**(8):`hsafe(s)` · `parse_dt(s)` · `load_tasks()` · `load_or_scaffold_plan(tasks)` · `compute_cpm(tasks)` · `schedule_dates(tasks, proj, start)` · `build_html(tasks, proj, start, cyclic_note, out_path)` · `main()`
- **CLI**:`--no-open`
- **自測**:主程式可跑

### VIA_ENG024_VmtProcessMining
- **族**:`functional modules/WorkOps/VMT/vmt_process_mining`(版本 1;現役 `vmt_process_mining.py`)
- **功能**:============================================================================
- **函式**(11):`norm_case(raw)` · `classify_activity(subject, from_self)` · `load_from_outlook()` · `load_from_vmt()` · `load_from_control()` · `load_sample()` · `mine_pandas(df)` · `mine_pm4py(df)` · `hum_dur(sec)` · `build_html(df, edges, perf, durations, act_freq)`
- **CLI**:`--no-open`
- **自測**:主程式可跑

### VIA_ENG025_VmtReplyIngest
- **族**:`functional modules/WorkOps/VMT/vmt_reply_ingest`(版本 1;現役 `vmt_reply_ingest.py`)
- **功能**:============================================================================
- **函式**(12):`now_iso()` · `hsafe(s)` · `append_event(evt, ref, detail)` · `load_ssot()` · `save_ssot(ss)` · `norm_case(s)` · `source_outlook()` · `source_inbox_file()` · `source_sample()` · `parse_replies(msgs, open_ids)`
- **CLI**:`--no-open`
- **自測**:主程式可跑

### VIA_ENG026_VmtSuperbomAttachRouter
- **族**:`functional modules/WorkOps/VMT/vmt_superbom_attach_router`(版本 1;現役 `vmt_superbom_attach_router.py`)
- **功能**:============================================================================
- **函式**(12):`now_iso()` · `md5_bytes(b)` · `norm_case(s)` · `append_event(evt, ref, detail)` · `load_ledger()` · `append_ledger(rec)` · `load_parser(parser_path)` · `source_outlook()` · `source_folder()` · `source_sample()`
- **CLI**:`--db` `--no-open` `--parser`
- **自測**:主程式可跑

### VIA_ENG027_VmtSuperbomBridge
- **族**:`functional modules/WorkOps/VMT/vmt_superbom_bridge`(版本 1;現役 `vmt_superbom_bridge.py`)
- **功能**:============================================================================
- **函式**(12):`now_iso()` · `load_ssot()` · `save_ssot(ss)` · `append_vmt_event(evt, ref, detail)` · `ensure_sbom_case(ss)` · `new_ids(ss)` · `existing_qref(ss)` · `make_mail(issue, q_reason, q_raw)` · `read_open_quarantine(con)` · `bridge_out(con, ss, mk_mail_dir)`
- **CLI**:`--commit` `--db` `--no-open`
- **自測**:主程式可跑

### VIA_ENG028_VmtSuperbomEventstream
- **族**:`functional modules/WorkOps/VMT/vmt_superbom_eventstream`(版本 1;現役 `vmt_superbom_eventstream.py`)
- **功能**:============================================================================
- **函式**(7):`to_dt(x)` · `read_superbom(con)` · `read_vmt_events(path, quids)` · `mine(df)` · `hum(sec)` · `build_html(df, edges, perf, durations, quids)` · `main()`
- **CLI**:`--db` `--no-open`
- **自測**:主程式可跑

### VIA_ENG029_VmtSurvey
- **族**:`functional modules/WorkOps/VMT/vmt_survey`(版本 1;現役 `vmt_survey.py`)
- **功能**:============================================================================
- **函式**(7):`hsafe(s)` · `load_pack()` · `build_form(out_path)` · `ingest()` · `score(ans)` · `apply_overrides(fx, dims)` · `main()`
- **CLI**:`--no-open`
- **自測**:主程式可跑

### VIA_ENG030_Init
- **族**:`functional modules/WorkOps/VTR/engine/tests/__init__`(版本 1;現役 `__init__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VIA_ENG031_TestEngine
- **族**:`functional modules/WorkOps/VTR/engine/tests/test_engine`(版本 1;現役 `test_engine.py`)
- **功能**:vtr_py 確定性層測試。
- **類**:TestDocument, TestConfig, TestGate, TestLangDetect, TestNormalize, TestProtect, _BadStage, TestInvariants, TestAdversarial, TestReplay, TestEndToEnd
- **函式**(3):`ctx()` · `doc_of(doc_id)` · `run(doc)`
- **自測**:主程式可跑

### VIA_ENG032_Init
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/__init__`(版本 1;現役 `__init__.py`)
- **功能**:vtr_py — DG-IN Meeting Transcript Restoration Engine（Python 版）。
- **自測**:匯入型

### VIA_ENG033_Cli
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/cli`(版本 1;現役 `cli.py`)
- **功能**:vtr CLI（確定性層）。
- **函式**(4):`cmd_restore(args)` · `cmd_replay(args)` · `cmd_inspect(args)` · `main(argv)`
- **CLI**:`--config` `--doc-id` `--meta` `--out` `--review` `--strict` `--to-rev`
- **自測**:主程式可跑

### VIA_ENG034_Context
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/context`(版本 1;現役 `context.py`)
- **功能**:執行期設定與 Context。
- **類**:Config, Metrics, Context
- **函式**(1):`default_config()`
- **自測**:匯入型

### VIA_ENG035_Document
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/document`(版本 1;現役 `document.py`)
- **功能**:VTR Document 資料契約的 Python 實作。
- **類**:ContractError, Run, Protection, Patch, Revision, Segment, Document
- **函式**(2):`apply_patches(segment, patches)` · `group_by_segment(patches)`
- **自測**:匯入型

### VIA_ENG036_Gate
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/gate`(版本 1;現役 `gate.py`)
- **功能**:信心度閘門（00_ARCHITECTURE.md §3）。
- **類**:ConfidenceGate
- **自測**:匯入型

### VIA_ENG037_Pipeline
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/pipeline`(版本 1;現役 `pipeline.py`)
- **功能**:Pipeline 執行器：Stage 串接、不變式檢查、patch 套用、版本記錄。
- **類**:StageResult, Stage, InvariantViolation, Pipeline
- **函式**(4):`check_invariants(before, result, stage_name)` · `commit(doc, result, stage_name, ctx, problems)` · `preprocessing_pipeline()` · `rejected_and_review(doc)`
- **自測**:匯入型

### VIA_ENG038_Protect
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/protect`(版本 1;現役 `protect.py`)
- **功能**:P0 保護遮罩（00_ARCHITECTURE.md §2.3）。
- **類**:Candidate, SentinelViolation
- **函式**(5):`find_candidates(text, enabled_kinds)` · `next_sentinel_index(segment)` · `mask(segment, candidates, make_patch_id)` · `unmask(segment, make_patch_id)` · `check_sentinels(segments)`
- **自測**:匯入型

### VIA_ENG039_Rules
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/rules`(版本 1;現役 `rules.py`)
- **功能**:rule_id 註冊表。
- **類**:Rule, UnknownRuleError
- **函式**(2):`require(rule_id, stage)` · `cross_engine_rule_ids()`
- **自測**:匯入型

### VIA_ENG040_Init
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/stages/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VTR Stage 實作。每個 Stage 都是純函式：(Document, Context) -> StageResult。
- **自測**:匯入型

### VIA_ENG041_S1LangDetect
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/stages/s1_lang_detect`(版本 1;現役 `s1_lang_detect.py`)
- **功能**:步驟 1：語言偵測（LANG_DETECT）。
- **類**:LangDetectStage
- **函式**(5):`classify(ch)` · `raw_runs(text)` · `merge_short_runs(runs, min_cjk, min_latin)` · `assign_roles(runs, text, dominant)` · `detect_segment(seg, min_cjk, min_latin, mixed_threshold)`
- **自測**:匯入型

### VIA_ENG042_S2Normalize
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/stages/s2_normalize`(版本 1;現役 `s2_normalize.py`)
- **功能**:步驟 2：正規化（NORMALIZE）。
- **類**:Claim, NormalizeStage
- **函式**(1):`resolve_claims(claims)`
- **自測**:匯入型

### VIA_ENG043_S3Protect
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/stages/s3_protect`(版本 1;現役 `s3_protect.py`)
- **功能**:P0：保護遮罩 Stage（PROTECT）。
- **類**:ProtectStage, UnprotectStage
- **自測**:匯入型

### VIA_ENG044_Init
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/versioning/__init__`(版本 1;現役 `__init__.py`)
- **功能**:Diff & Versioning Pipeline。
- **自測**:匯入型

### VIA_ENG045_Patchlog
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/versioning/patchlog`(版本 1;現役 `patchlog.py`)
- **功能**:append-only patch log（JSONL）。
- **函式**(3):`write_patchlog(doc, path)` · `read_patchlog(path)` · `patches_of_rev(rows, rev)`
- **自測**:匯入型

### VIA_ENG046_Replay
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/versioning/replay`(版本 1;現役 `replay.py`)
- **功能**:重播與回滾。
- **類**:ReplayMismatch
- **函式**(1):`replay_to(doc, target_rev)`
- **自測**:匯入型

### VIA_ENG047_ValidateLexicon
- **族**:`functional modules/WorkOps/VTR/lexicon/tools/validate_lexicon`(版本 1;現役 `validate_lexicon.py`)
- **功能**:VTR SSOT Lexicon validator / indexer.
- **類**:Report
- **函式**(7):`sha256_of(path)` · `load_files(rep)` · `check_structure(name, doc, rep)` · `check_ssot(docs, rep)` · `check_with_jsonschema(docs, rep)` · `build_index(docs)` · `main()`
- **CLI**:`--quiet` `--write-index`
- **自測**:主程式可跑

### VIA_ENG048_BuildManifest
- **族**:`functional modules/WorkOps/VTR/tools/build_manifest`(版本 1;現役 `build_manifest.py`)
- **功能**:重算 VTR_Subsystem_Manifest.json。
- **函式**(7):`content_hash(path)` · `content_size(path)` · `sha256_of(path)` · `collect_artifacts()` · `build()` · `serialize(manifest)` · `main()`
- **CLI**:`--quiet` `--write`
- **自測**:主程式可跑

### VIA_ENG049_TestV0106Accuracy
- **族**:`functional modules/WorkOps/candidates/accuracy_center_external_v0100/test_v0106_accuracy`(版本 1;現役 `test_v0106_accuracy.py`)
- **功能**:無說明(候補)
- **函式**(2):`run(eng, work, script)` · `test_accuracy_hard_gates()`
- **自測**:匯入型

### VIA_ENG050_WorkopsCommitmentIntelligence
- **族**:`functional modules/WorkOps/candidates/eng050_053_external_v0100/engines/workops_commitment_intelligence`(版本 1;現役 `workops_commitment_intelligence.py`)
- **功能**:Veritas WorkOps Commitment Intelligence v0100 (ENG-051)
- **函式**(11):`load()` · `save(d)` · `existing_source_refs(d)` · `candidates()` · `create(wop, what, owner, due, source_ref)` · `accept(candidate_id)` · `state(cid, status, reason)` · `reschedule(cid, due, reason)` · `fulfill(cid, evidence)` · `status_doc()`
- **CLI**:`--due` `--evidence` `--reason` `--source`
- **自測**:主程式可跑

### VIA_ENG051_WorkopsConsistencyGuard
- **族**:`functional modules/WorkOps/candidates/eng050_053_external_v0100/engines/workops_consistency_guard`(版本 1;現役 `workops_consistency_guard.py`)
- **功能**:Veritas WorkOps Cross-Ledger Consistency Guard v0100 (ENG-052)
- **函式**(4):`finding(rows, code, wop, native, detail)` · `cycle_find(nodes, edges)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG052_WorkopsControlCommon
- **族**:`functional modules/WorkOps/candidates/eng050_053_external_v0100/engines/workops_control_common`(版本 1;現役 `workops_control_common.py`)
- **功能**:無說明(候補)
- **函式**(12):`now()` · `today()` · `jload(p, d)` · `csvrows(p)` · `atomic_json(p, obj)` · `append_hist(item, ev, detail)` · `wop_registry()` · `thr2wop()` · `project_label(wop)` · `decision_rows()`
- **自測**:匯入型

### VIA_ENG053_WorkopsProjectHealth
- **族**:`functional modules/WorkOps/candidates/eng050_053_external_v0100/engines/workops_project_health`(版本 1;現役 `workops_project_health.py`)
- **功能**:Veritas WorkOps Explainable Project Health & Progress v0100 (ENG-053)
- **函式**(4):`ratio(done, total)` · `cap(each, n, capv)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG054_WorkopsUnifiedWorkRegister
- **族**:`functional modules/WorkOps/candidates/eng050_053_external_v0100/engines/workops_unified_work_register`(版本 1;現役 `workops_unified_work_register.py`)
- **功能**:Veritas WorkOps Unified Work Register v0100 (ENG-050)
- **函式**(3):`add(rows, typ, native, wop, title)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG055_EmailActionDb
- **族**:`functional modules/WorkOps/engines/email_action_db`(版本 1;現役 `email_action_db.py`)
- **功能**:email_action_db.py  v1.0
- **類**:_HtmlToText
- **函式**(12):`html_to_text(raw)` · `repair_bytes(raw, declared)` · `repair_mojibake(text)` · `strip_noise(text)` · `repair_body(msg)` · `load_eml(path)` · `load_msg(path)` · `load_txt(path)` · `load_csv_file(path)` · `ingest(input_path)`
- **CLI**:`--db` `--export` `--input` `--report` `--since`
- **自測**:主程式可跑

### VIA_ENG056_EmailSuperEngine
- **族**:`functional modules/WorkOps/engines/email_super_engine`(版本 1;現役 `email_super_engine.py`)
- **功能**:email_super_engine.py  v1.1
- **類**:_H2T
- **函式**(12):`progress(pct, label)` · `load_rules_addendum(path)` · `normalize_deadline(raw, anchor)` · `html_to_text(raw)` · `repair_bytes(raw, declared)` · `repair_mojibake(text)` · `strip_noise(text)` · `repair_body(msg)` · `load_eml(path)` · `load_msg(path)`
- **CLI**:`--input` `--no-xlsx` `--outdir` `--report` `--since` `--ssot`
- **自測**:主程式可跑

### VIA_ENG057_EngineAnalytics
- **族**:`functional modules/WorkOps/engines/engine_analytics`(版本 1;現役 `engine_analytics.py`)
- **功能**:engine_analytics.py  v1.3
- **函式**(11):`progress(pct, label)` · `load_domain_dict(path)` · `textrank_keywords(text, top_n)` · `tokenize(text)` · `nlp_case_keywords(conn, top_n)` · `nlp_cluster_unclassified(conn, max_k)` · `nlp_supervised_suggest(conn, min_train, confidence)` · `nlp_similar_threads(conn, threshold)` · `dm_latency_outliers(conn)` · `dm_weekly_volume(conn)`
- **CLI**:`--db` `--outdir`
- **自測**:主程式可跑

### VIA_ENG058_WorkopsAccuracyBenchmark
- **族**:`functional modules/WorkOps/engines/workops_accuracy_benchmark`(版本 1;現役 `workops_accuracy_benchmark.py`)
- **功能**:WorkOps Gold Set 準確度基準 v0101(ENG-030)— v0200 RC 驗收 Gate E 補強落地
- **函式**(6):`load_json(p, default)` · `current_state()` · `cmd_template()` · `cmd_run(csvpath)` · `cmd_auto()` · `main()`
- **自測**:主程式可跑

### VIA_ENG059_WorkopsAccuracyHarness
- **族**:`functional modules/WorkOps/engines/workops_accuracy_harness`(版本 1;現役 `workops_accuracy_harness.py`)
- **功能**:WorkOps 受控正確率驗證 harness v0100(ENG-050)— 操作員「大幅提高正確率各類方法」令
- **函式**(2):`C(cid, desc, layer, status, subject)` · `run()`
- **自測**:主程式可跑

### VIA_ENG060_WorkopsAuditBundle
- **族**:`functional modules/WorkOps/engines/workops_audit_bundle`(版本 1;現役 `workops_audit_bundle.py`)
- **功能**:Veritas WorkOps 稽核包引擎 v0100(ENG-036)— 六機制研究第六項「audit bundle」落地
- **函式**(4):`sha16(b)` · `redline_scan()` · `newest(pattern, root)` · `build()`
- **自測**:主程式可跑

### VIA_ENG061_WorkopsBackup
- **族**:`functional modules/WorkOps/engines/workops_backup`(版本 1;現役 `workops_backup.py`)
- **功能**:WorkOps 備份/驗證/還原到暫存 v0100(ENG-031)— v0200 RC 驗收 L06 安全車道補強落地
- **函式**(5):`sha256(p)` · `cmd_backup()` · `cmd_verify(zippath)` · `cmd_restore(zippath)` · `main()`
- **自測**:主程式可跑

### VIA_ENG062_WorkopsClosureIntelligence
- **族**:`functional modules/WorkOps/engines/workops_closure_intelligence`(版本 1;現役 `workops_closure_intelligence.py`)
- **功能**:Veritas WorkOps 案件結案智能 v0100 — GapFill 自建路 B(裁定序 E;候選+顯式確認)
- **函式**(7):`jload(p, d)` · `now()` · `open_decisions()` · `cmd_build()` · `cmd_confirm(wop, reason)` · `cmd_list()` · `main(argv)`
- **CLI**:`--reason`
- **自測**:主程式可跑

### VIA_ENG063_WorkopsCommitmentIntelligence
- **族**:`functional modules/WorkOps/engines/workops_commitment_intelligence`(版本 1;現役 `workops_commitment_intelligence.py`)
- **功能**:Veritas WorkOps Commitment Intelligence v0100(ENG-051;與外部套件對照碼同號)
- **函式**(11):`load()` · `save(d)` · `existing_source_refs(d)` · `candidates()` · `create(wop, what, owner, due, source_ref)` · `accept(candidate_id)` · `state(cid, status, reason)` · `reschedule(cid, due, reason)` · `fulfill(cid, evidence)` · `status_doc()`
- **CLI**:`--due` `--evidence` `--reason` `--source`
- **自測**:主程式可跑

### VIA_ENG064_WorkopsConsistencyGuard
- **族**:`functional modules/WorkOps/engines/workops_consistency_guard`(版本 1;現役 `workops_consistency_guard.py`)
- **功能**:Veritas WorkOps Cross-Ledger Consistency Guard v0100(ENG-052;與外部套件對照碼同號)
- **函式**(4):`finding(rows, code, wop, native, detail)` · `cycle_find(nodes, edges)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG065_WorkopsControlCommon
- **族**:`functional modules/WorkOps/engines/workops_control_common`(版本 1;現役 `workops_control_common.py`)
- **功能**:無說明(候補)
- **函式**(12):`now()` · `today()` · `jload(p, d)` · `csvrows(p)` · `atomic_json(p, obj)` · `append_hist(item, ev, detail)` · `wop_registry()` · `thr2wop()` · `project_label(wop)` · `decision_rows()`
- **自測**:匯入型

### VIA_ENG066_WorkopsCorpusBridge
- **族**:`functional modules/WorkOps/engines/workops_corpus_bridge`(版本 1;現役 `workops_corpus_bridge.py`)
- **功能**:無說明(候補)
- **函式**(4):`norm_date(v)` · `map_row(row)` · `collect(paths)` · `main()`
- **CLI**:`--inputs` `--outdir`
- **自測**:主程式可跑

### VIA_ENG067_WorkopsDailyTodo
- **族**:`functional modules/WorkOps/engines/workops_daily_todo`(版本 1;現役 `workops_daily_todo.py`)
- **功能**:Veritas WorkOps 每日 TO-DO 引擎 v0102(ENG-046)— 同類工作一口氣,三時間錨
- **函式**(4):`jload(p, d)` · `rows(p)` · `fill(tpl)` · `build()`
- **自測**:主程式可跑

### VIA_ENG068_WorkopsDecisionLog
- **族**:`functional modules/WorkOps/engines/workops_decision_log`(版本 1;現役 `workops_decision_log.py`)
- **功能**:無說明(候補)
- **函式**(10):`conn()` · `now()` · `next_id(c)` · `hist(c, did, action, value)` · `cmd_add(what, owner, due, source, meeting)` · `cmd_list(status)` · `cmd_status(did, new_status, note)` · `cmd_report()` · `cmd_export()` · `main()`
- **自測**:主程式可跑

### VIA_ENG069_WorkopsEnvmanagerBridge
- **族**:`functional modules/WorkOps/engines/workops_envmanager_bridge`(版本 1;現役 `workops_envmanager_bridge.py`)
- **功能**:無說明(候補)
- **函式**(6):`find_envmanager()` · `load_envmanager(em_path, venv_dir, outdir)` · `cmd_health(em, venv_dir)` · `cmd_plan(em, venv_dir, package, version)` · `cmd_install(em, venv_dir, package, version, wheels_only)` · `main()`
- **CLI**:`--only-binary=:all:` `--outdir` `--venv` `--wheels-only`
- **自測**:主程式可跑

### VIA_ENG070_WorkopsGraphvizSetup
- **族**:`functional modules/WorkOps/engines/workops_graphviz_setup`(版本 1;現役 `workops_graphviz_setup.py`)
- **功能**:無說明(候補)
- **函式**(7):`find_portable_dot()` · `find_dot()` · `http_get(url, to_file)` · `verify_dot(dot)` · `cmd_status()` · `cmd_install(force)` · `main()`
- **CLI**:`--force`
- **自測**:主程式可跑

### VIA_ENG071_WorkopsLessonLearned
- **族**:`functional modules/WorkOps/engines/workops_lesson_learned`(版本 1;現役 `workops_lesson_learned.py`)
- **功能**:Veritas WorkOps 教訓引擎 v0100 — GapFill 自建路 B(裁定序 F;候選+顯式確認)
- **函式**(6):`jload(p, d)` · `now()` · `cmd_build()` · `cmd_confirm(idx, root_cause, prevention, reuse_rule)` · `cmd_list()` · `main(argv)`
- **CLI**:`--prevention` `--reuse-rule` `--root-cause`
- **自測**:主程式可跑

### VIA_ENG072_WorkopsLexicon
- **族**:`functional modules/WorkOps/engines/workops_lexicon`(版本 1;現役 `workops_lexicon.py`)
- **功能**:WorkOps 共用詞彙模組 v0101 — SSOT/REGEX/同義字/LIST 彙整去重(操作員 2026/08/09 令)。
- **函式**(7):`norm_subj(s)` · `clean_subject(s)` · `subj_code(s)` · `load_bulk_patterns(path)` · `is_bulk(sender, pats)` · `load_org_lexicon(path)` · `extract_url_domains(text)`
- **自測**:匯入型

### VIA_ENG073_WorkopsMeetingloopBridge
- **族**:`functional modules/WorkOps/engines/workops_meetingloop_bridge`(版本 1;現役 `workops_meetingloop_bridge.py`)
- **功能**:Veritas WorkOps × MeetingLoop 對帳橋 v0100(ENG-048)— 操作員「合為對帳」令
- **函式**(5):`jload(p, d)` · `key_of(mtg, text)` · `cmd_pull()` · `cmd_status()` · `main(argv)`
- **自測**:主程式可跑

### VIA_ENG074_WorkopsMilestoneManager
- **族**:`functional modules/WorkOps/engines/workops_milestone_manager`(版本 1;現役 `workops_milestone_manager.py`)
- **功能**:Veritas WorkOps 里程碑引擎 v0100 — GapFill 自建路 B(裁定序 C;append-only)
- **函式**(8):`now()` · `load()` · `save(d)` · `cmd_create(wop, name, due, owner)` · `cmd_complete(mid, evidence)` · `cmd_list(wop)` · `cmd_status()` · `main(argv)`
- **CLI**:`--evidence` `--owner`
- **自測**:主程式可跑

### VIA_ENG075_WorkopsMlLab
- **族**:`functional modules/WorkOps/engines/workops_ml_lab`(版本 1;現役 `workops_ml_lab.py`)
- **功能**:WorkOps ML 實驗室 v0101(ENG-055)— 操作員 apply ML/DL top10 local free libs 令
- **函式**(10):`now()` · `cfg()` · `need_sklearn()` · `cmd_probe()` · `cmd_setup()` · `cmd_train()` · `cmd_suggest()` · `cmd_cluster()` · `cmd_adopt()` · `main()`
- **CLI**:`--user`
- **自測**:主程式可跑

### VIA_ENG076_WorkopsNamer
- **族**:`functional modules/WorkOps/engines/workops_namer`(版本 1;現役 `workops_namer.py`)
- **功能**:無說明(候補)
- **函式**(10):`link_thr_to_case(led, dbpath)` · `now()` · `load_ledger()` · `save_ledger(led)` · `propose_name(subjects, senders)` · `cmd_propose(dbpath)` · `cmd_apply(csvpath)` · `cmd_add(name, keyword)` · `cmd_list()` · `main()`
- **CLI**:`--csv` `--db`
- **自測**:主程式可跑

### VIA_ENG077_WorkopsOnboarding
- **族**:`functional modules/WorkOps/engines/workops_onboarding`(版本 1;現役 `workops_onboarding.py`)
- **功能**:Veritas WorkOps 首跑狀態機 v0100 — GapFill 自建路 B(裁定序 B;唯讀評估)
- **函式**(2):`jload(p, d)` · `build()`
- **自測**:主程式可跑

### VIA_ENG078_WorkopsProjectHealth
- **族**:`functional modules/WorkOps/engines/workops_project_health`(版本 1;現役 `workops_project_health.py`)
- **功能**:Veritas WorkOps Explainable Project Health & Progress v0100(ENG-053;與外部套件對照碼同號)
- **函式**(4):`ratio(done, total)` · `cap(each, n, capv)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG079_WorkopsReplyParser
- **族**:`functional modules/WorkOps/engines/workops_reply_parser`(版本 1;現役 `workops_reply_parser.py`)
- **功能**:WorkOps 回覆解析引擎 v0106(ENG-029)— 規劃書 M3:回信 → 三層 fallback 解析 → 狀態事件
- **函式**(12):`load_json(p, default)` · `load_params()` · `read_csv(p)` · `load_scan_index()` · `norm_subject(s)` · `load_corpus_bodies()` · `body_for(bodies, corpus, conv, subject)` · `detect_flags(row, body, params)` · `parse_one(row, body, params)` · `load_seen()`
- **自測**:主程式可跑

### VIA_ENG080_WorkopsRetentionManager
- **族**:`functional modules/WorkOps/engines/workops_retention_manager`(版本 1;現役 `workops_retention_manager.py`)
- **功能**:Veritas WorkOps 保留政策引擎 v0100 — GapFill 自建路 B(裁定序 G;PLAN 先行·apply 特別門)
- **函式**(7):`params()` · `aged_dirs(root, days)` · `build_plan()` · `cmd_plan()` · `cmd_apply(confirm)` · `cmd_log()` · `main(argv)`
- **CLI**:`--confirm`
- **自測**:主程式可跑

### VIA_ENG081_WorkopsSelftest
- **族**:`functional modules/WorkOps/engines/workops_selftest`(版本 1;現役 `workops_selftest.py`)
- **功能**:Veritas WorkOps 全鏈自測器 v0104(ENG-032)— Integration + System Test 一鍵版
- **函式**(4):`stage(name, ok, detail)` · `run_py(sandbox, script)` · `build_fixtures(sb)` · `main()`
- **CLI**:`--evidence` `--owner` `--prevention` `--reason` `--root-cause`
- **自測**:主程式可跑

### VIA_ENG082_WorkopsSlides
- **族**:`functional modules/WorkOps/engines/workops_slides`(版本 1;現役 `workops_slides.py`)
- **功能**:Veritas WorkOps 自動簡報引擎 v0100(ENG-033)— 板資料 → 週報 slides(候令開工:UI 重規劃 §4.4)
- **函式**(7):`jload(p, default)` · `csv_rows(p)` · `esc(s)` · `bar(pc, color)` · `missing(what)` · `gather()` · `build()`
- **自測**:主程式可跑

### VIA_ENG083_WorkopsSummaryMatrix
- **族**:`functional modules/WorkOps/engines/workops_summary_matrix`(版本 1;現役 `workops_summary_matrix.py`)
- **功能**:Veritas WorkOps 總結矩陣引擎 v0100(ENG-037)— DETAILED SUMMARY MATRIX:RESULT + DB
- **函式**(10):`fsize(n)` · `stat_row(name, p, note)` · `jload(p)` · `csv_n(p)` · `jsonl_n(p)` · `newest(root, pattern)` · `sqlite_info(p)` · `gather()` · `esc(s)` · `build()`
- **自測**:主程式可跑

### VIA_ENG084_WorkopsTimelineDependency
- **族**:`functional modules/WorkOps/engines/workops_timeline_dependency`(版本 1;現役 `workops_timeline_dependency.py`)
- **功能**:Veritas WorkOps 時間軸/依賴引擎 v0100 — GapFill 自建路 B(裁定序 D;append-only 連結)
- **函式**(5):`jload(p, d)` · `cmd_link(a, b)` · `cmd_build()` · `cmd_list()` · `main(argv)`
- **自測**:主程式可跑

### VIA_ENG085_WorkopsUnifiedSearch
- **族**:`functional modules/WorkOps/engines/workops_unified_search`(版本 1;現役 `workops_unified_search.py`)
- **功能**:Veritas WorkOps 統一搜尋引擎 v0100 — GapFill 自建路 B(裁定序 A;全唯讀)
- **函式**(4):`jload(p, d)` · `rows(p)` · `hit(terms)` · `main(argv)`
- **自測**:主程式可跑

### VIA_ENG086_WorkopsUnifiedWorkRegister
- **族**:`functional modules/WorkOps/engines/workops_unified_work_register`(版本 1;現役 `workops_unified_work_register.py`)
- **功能**:Veritas WorkOps Unified Work Register v0100(ENG-054;外部套件對照碼 ENG-050)
- **函式**(3):`add(rows, typ, native, wop, title)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG087_WorkopsWopIdentifier
- **族**:`functional modules/WorkOps/engines/workops_wop_identifier`(版本 1;現役 `workops_wop_identifier.py`)
- **功能**:WorkOps WOP 識別歸戶引擎 v0109(ENG-028)— 規劃書 M1+M2:bottom-up 多訊號融合 → WOP 專案化+賦號
- **函式**(12):`sheet_normalize(rows, params)` · `load_folder_map()` · `load_product_rules()` · `rule_match(rule, subj, dom, attach)` · `folder_blacklisted(name, params)` · `now()` · `load_params()` · `load_json(p, default)` · `read_csv(p)` · `control_sheet_rows(params)`
- **自測**:主程式可跑

### VIA_ENG088_BoardQa
- **族**:`functional modules/WorkOps/qa/board_qa`(版本 1;現役 `board_qa.py`)
- **功能**:board_qa.py v0100 — 指揮板四層測試(操作員「unit/integration/system test + u/i sync」令)。
- **函式**(5):`newest_board()` · `extract(board_src)` · `tier_design(board_src)` · `run_node(script)` · `main()`
- **CLI**:`--color-accent` `--color-accent-2` `--color-bg` `--color-surface` `--color-text`
- **自測**:主程式可跑

### VIA_ENG089_Init
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/engine/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VIA Accelerated Integration v0139A governed engines.
- **自測**:匯入型

### VIA_ENG090_DomainEngine
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/engine/via_domain_engine`(版本 1;現役 `via_domain_engine_v0139a.py`)
- **功能**:無說明(候補)
- **類**:ContractError, HydraRiskError, WriteResult, PipelineResult
- **函式**(12):`def_utc_now_text()` · `def_slug(value)` · `def_sha256_bytes(data)` · `def_sha256_file(path)` · `def_atomic_write_text(path, content, encoding)` · `def_atomic_write_json(path, payload)` · `def_normalize_columns(frame, aliases)` · `def_require_columns(frame, required, dataset_name)` · `def_normalize_ticker(value)` · `def_read_table(path, declared_format)`
- **CLI**:`--classification` `--flows` `--mode` `--output-dir` `--prices` `--require-parquet` `--revenue`
- **自測**:主程式可跑

### VIA_ENG091_FlowSimulationEngine
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/engine/via_flow_simulation_engine`(版本 1;現役 `via_flow_simulation_engine_v0139a.py`)
- **功能**:無說明(候補)
- **函式**(1):`def_run(flows, prices, classification, short_window, long_window)`
- **自測**:匯入型

### VIA_ENG092_GroupIndexEngine
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/engine/via_group_index_engine`(版本 1;現役 `via_group_index_engine_v0139a.py`)
- **功能**:無說明(候補)
- **函式**(1):`def_run(prices, classification, group_column, weighting, base_value)`
- **自測**:匯入型

### VIA_ENG093_MonthlyRevenueAnalysisEngine
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/engine/via_monthly_revenue_analysis_engine`(版本 1;現役 `via_monthly_revenue_analysis_engine_v0139a.py`)
- **功能**:無說明(候補)
- **函式**(1):`def_run(revenue, classification)`
- **自測**:匯入型

### VIA_ENG094_StockGroupClassificationEngine
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/engine/via_stock_group_classification_engine`(版本 1;現役 `via_stock_group_classification_engine_v0139a.py`)
- **功能**:無說明(候補)
- **函式**(1):`def_run(classification)`
- **自測**:匯入型

### VIA_ENG095_VapUpdateEngine
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/engine/via_vap_update_engine`(版本 1;現役 `via_vap_update_engine_v0139a.py`)
- **功能**:無說明(候補)
- **函式**(1):`def_render(output_path, group_index, flow_daily, flow_summary, revenue_group)`
- **自測**:匯入型

### VIA_ENG096_Init
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/tests/__init__`(版本 1;現役 `__init__.py`)
- **功能**:Unit and integration tests for VIA Accelerated Integration v0139A.
- **自測**:匯入型

### VIA_ENG097_TestViaAcceleratedIntegration
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/tests/test_via_accelerated_integration`(版本 1;現役 `test_via_accelerated_integration_v0139a.py`)
- **功能**:無說明(候補)
- **類**:ViaAcceleratedIntegrationTests
- **自測**:主程式可跑

### VIA_ENG098_WorkopsFollowupPackBuilder
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/docs/history/v0106_variants/engines/workops_followup_pack_builder`(版本 1;現役 `workops_followup_pack_builder.py`)
- **功能**:ENG-034 Batch Follow-up Pack Builder.
- **函式**(9):`loadj(p, d)` · `loadjl(p)` · `atomic(p, obj)` · `latest_projects()` · `template_registry()` · `template_by_key(key)` · `render(s, ctx)` · `build(language, template_override)` · `main()`
- **CLI**:`--language` `--template`
- **自測**:主程式可跑

### VIA_ENG099_WorkopsFollowupState
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/docs/history/v0106_variants/engines/workops_followup_state`(版本 1;現役 `workops_followup_state.py`)
- **功能**:ENG-030 WorkOps Follow-up State Engine v0100.
- **類**:Handler
- **函式**(12):`load_json(path, default)` · `load_jsonl(path)` · `atomic_write_json(path, obj)` · `parse_dt(v)` · `hours_since(v, now)` · `score_to_level(score, params)` · `read_wop_map()` · `latest_reply_events()` · `closed_map()` · `compute_state()`
- **CLI**:`--no-open`
- **自測**:主程式可跑

### VIA_ENG100_WorkopsModuleLifecycleManager
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/docs/history/v0106_variants/engines/workops_module_lifecycle_manager`(版本 1;現役 `workops_module_lifecycle_manager.py`)
- **功能**:無說明(候補)
- **函式**(7):`loadj(p, d)` · `sha(p)` · `atomic(p, o)` · `append(p, o)` · `health()` · `propose(mid, candidate, notes)` · `main()`
- **CLI**:`--notes`
- **自測**:主程式可跑

### VIA_ENG101_WorkopsProgressEstimator
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/docs/history/v0106_variants/engines/workops_progress_estimator`(版本 1;現役 `workops_progress_estimator.py`)
- **功能**:ENG-049 Evidence-based Project Progress Estimator.
- **函式**(5):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG102_WorkopsProjectCardAggregator
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/docs/history/v0106_variants/engines/workops_project_card_aggregator`(版本 1;現役 `workops_project_card_aggregator.py`)
- **功能**:ENG-038 Project Card Aggregator.
- **函式**(6):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `latest_projects()` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG103_WorkopsProjectFusion
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/docs/history/v0106_variants/engines/workops_project_fusion`(版本 1;現役 `workops_project_fusion.py`)
- **功能**:ENG-032 Project Fusion Classifier.
- **函式**(12):`loadj(p, d)` · `loadjl(p)` · `readcsv(p)` · `pick(r, names)` · `toks(s)` · `sim(a, b)` · `control_sheet_rows()` · `latest_projects()` · `confirmed_memory()` · `extract_codes(text, pats)`
- **自測**:主程式可跑

### VIA_ENG104_WorkopsAccuracyBenchmark
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_accuracy_benchmark`(版本 1;現役 `workops_accuracy_benchmark.py`)
- **功能**:ENG-055 Gold-set benchmark + confidence calibration error.
- **函式**(4):`jl(p)` · `metric(gold, pred, field)` · `build(gold_path, pred_path)` · `main()`
- **自測**:主程式可跑

### VIA_ENG105_WorkopsApiServer
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_api_server`(版本 1;現役 `workops_api_server.py`)
- **功能**:Localhost-only FastAPI product server.
- **類**:ProjectCreate, ProjectConfirm, FollowupBuild, ClosureConfirm, DraftCreate, OnboardingComplete, MilestoneCreate, MilestoneComplete, StakeholderConfirm, OutlookConfigUpdate
- **函式**(12):`j(path, default)` · `cmd(script, args, timeout)` · `root()` · `status()` · `get_outlook_config()` · `set_outlook_config(x)` · `upload_control_sheet(file)` · `sync()` · `refresh()` · `cards()`
- **CLI**:`--language` `--template`
- **自測**:主程式可跑

### VIA_ENG106_WorkopsAttachmentIntelligence
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_attachment_intelligence`(版本 1;現役 `workops_attachment_intelligence.py`)
- **功能**:ENG-065 Local attachment metadata/text parser. No OCR.
- **函式**(6):`jl(p)` · `attachment_sys_id(message_graph_id, attachment_id)` · `sha(p)` · `text_of(p)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG107_WorkopsAutocode
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_autocode`(版本 1;現役 `workops_autocode.py`)
- **功能**:Shared immutable auto-code component.
- **類**:_Lock
- **函式**(1):`next_code(prefix, event_date, width)`
- **自測**:匯入型

### VIA_ENG108_WorkopsBackupRestore
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_backup_restore`(版本 1;現役 `workops_backup_restore.py`)
- **功能**:ENG-057 Backup, verify, and restore-to-staging. Token cache excluded by default.
- **函式**(7):`jload(p, d)` · `sha(p)` · `excluded(rel, patterns)` · `backup()` · `verify(zpath)` · `restore(zpath)` · `main()`
- **自測**:主程式可跑

### VIA_ENG109_WorkopsClosureIntelligence
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_closure_intelligence`(版本 1;現役 `workops_closure_intelligence.py`)
- **功能**:無說明(候補)
- **函式**(9):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `append(p, o)` · `closed()` · `rebuild_status()` · `detect()` · `confirm(project_id, case_id, thr, reason, confirmed_by)` · `main()`
- **CLI**:`--case-id` `--confirmed-by` `--project-id` `--reason` `--thr`
- **自測**:主程式可跑

### VIA_ENG110_WorkopsCommitmentFulfillment
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_commitment_fulfillment`(版本 1;現役 `workops_commitment_fulfillment.py`)
- **功能**:ENG-043 Commitment Fulfillment Engine.
- **函式**(12):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `append(p, o)` · `now()` · `parse_dt(s)` · `current_registry()` · `scan()` · `confirm(index)` · `evaluate()`
- **CLI**:`--evidence` `--new-due` `--reason`
- **自測**:主程式可跑

### VIA_ENG111_WorkopsConfidenceCalibrator
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_confidence_calibrator`(版本 1;現役 `workops_confidence_calibrator.py`)
- **功能**:ENG-047 Confidence Calibration & Accuracy Gate.
- **函式**(7):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `band(score, policy)` · `signal_kind(e)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG112_WorkopsDailyOperatingRhythm
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_daily_operating_rhythm`(版本 1;現役 `workops_daily_operating_rhythm.py`)
- **功能**:ENG-041 Daily Operating Rhythm.
- **函式**(11):`loadj(p, d)` · `atomic(p, o)` · `append(p, o)` · `now_local(override)` · `hm(s)` · `current_phase(now, p)` · `key_of(x)` · `unique(rows)` · `action(label_zh, label_cn, label_en, src, kind)` · `build(override_now)`
- **CLI**:`--now`
- **自測**:主程式可跑

### VIA_ENG113_WorkopsDiagnostics
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_diagnostics`(版本 1;現役 `workops_diagnostics.py`)
- **功能**:ENG-058 Diagnostics + IT governance evidence.
- **函式**(4):`jload(p, d)` · `exists(rel)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG114_WorkopsEvidenceIntegrityGuard
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_evidence_integrity_guard`(版本 1;現役 `workops_evidence_integrity_guard.py`)
- **功能**:ENG-046 Evidence Integrity & Contradiction Guard.
- **函式**(6):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `project_latest()` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG115_WorkopsFeedbackWeightOptimizer
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_feedback_weight_optimizer`(版本 1;現役 `workops_feedback_weight_optimizer.py`)
- **功能**:ENG-048 Feedback Weight Optimizer.
- **函式**(5):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG116_WorkopsFollowupPackBuilder
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_followup_pack_builder`(版本 1;現役 `workops_followup_pack_builder.py`)
- **功能**:ENG-034 Batch Follow-up Pack Builder.
- **函式**(9):`loadj(p, d)` · `loadjl(p)` · `atomic(p, obj)` · `latest_projects()` · `template_registry()` · `template_by_key(key)` · `render(s, ctx)` · `build(language, template_override)` · `main()`
- **CLI**:`--language` `--template`
- **自測**:主程式可跑

### VIA_ENG117_WorkopsFollowupState
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_followup_state`(版本 1;現役 `workops_followup_state.py`)
- **功能**:ENG-030 WorkOps Follow-up State Engine v0100.
- **類**:Handler
- **函式**(12):`load_json(path, default)` · `load_jsonl(path)` · `atomic_write_json(path, obj)` · `parse_dt(v)` · `hours_since(v, now)` · `score_to_level(score, params)` · `read_wop_map()` · `latest_reply_events()` · `closed_map()` · `compute_state()`
- **CLI**:`--no-open`
- **自測**:主程式可跑

### VIA_ENG118_WorkopsLessonLearned
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_lesson_learned`(版本 1;現役 `workops_lesson_learned.py`)
- **功能**:ENG-044 Lesson Learned Engine.
- **函式**(7):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `append(p, o)` · `build()` · `confirm(index, root_cause, prevention, reuse_rule)` · `main()`
- **CLI**:`--prevention` `--reuse-rule` `--root-cause`
- **自測**:主程式可跑

### VIA_ENG119_WorkopsMailEventBridge
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_mail_event_bridge`(版本 1;現役 `workops_mail_event_bridge.py`)
- **功能**:ENG-061 bridge normalized Outlook mail into the standalone Follow-up State contract.
- **函式**(9):`jload(p, d)` · `jl(p)` · `latest_projects()` · `project_map()` · `parse_status(text, p)` · `extract_date(text)` · `extract_label(text, labels)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG120_WorkopsMandatoryReplyBuilder
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_mandatory_reply_builder`(版本 1;現役 `workops_mandatory_reply_builder.py`)
- **功能**:ENG-031 Mandatory Reply Builder.
- **函式**(6):`loadj(p, d)` · `atomic(p, obj)` · `build_questions(card, params)` · `render_body(card, questions, fup_id)` · `build()` · `main()`
- **CLI**:`---`
- **自測**:主程式可跑

### VIA_ENG121_WorkopsMeetingT2Guard
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_meeting_t2_guard`(版本 1;現役 `workops_meeting_t2_guard.py`)
- **功能**:ENG-042 Meeting T-2 Preparation Guard.
- **函式**(7):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `now()` · `dt(s)` · `build(override_now)` · `main()`
- **CLI**:`--now`
- **自測**:主程式可跑

### VIA_ENG122_WorkopsMilestoneManager
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_milestone_manager`(版本 1;現役 `workops_milestone_manager.py`)
- **功能**:ENG-063 Append-only project milestone manager.
- **函式**(7):`jl(p)` · `append(o)` · `current()` · `build()` · `create(project_id, name, target_date, owner, weight)` · `complete(mid, evidence, actual_date)` · `main()`
- **CLI**:`--actual-date` `--evidence` `--owner` `--weight`
- **自測**:主程式可跑

### VIA_ENG123_WorkopsMissingInformationGuard
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_missing_information_guard`(版本 1;現役 `workops_missing_information_guard.py`)
- **功能**:ENG-037 Missing Information Guard: converts vague work into explicit missing controls.
- **函式**(4):`loadj(p, d)` · `atomic(p, o)` · `scan()` · `main()`
- **自測**:主程式可跑

### VIA_ENG124_WorkopsModuleLifecycleManager
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_module_lifecycle_manager`(版本 1;現役 `workops_module_lifecycle_manager.py`)
- **功能**:無說明(候補)
- **函式**(7):`loadj(p, d)` · `sha(p)` · `atomic(p, o)` · `append(p, o)` · `health()` · `propose(mid, candidate, notes)` · `main()`
- **CLI**:`--notes`
- **自測**:主程式可跑

### VIA_ENG125_WorkopsOnboarding
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_onboarding`(版本 1;現役 `workops_onboarding.py`)
- **功能**:ENG-059 Onboarding state machine.
- **函式**(5):`jload(p, d)` · `status()` · `complete(key)` · `reset()` · `main()`
- **自測**:主程式可跑

### VIA_ENG126_WorkopsOrchestrator
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_orchestrator`(版本 1;現役 `workops_orchestrator.py`)
- **功能**:ENG-060 central WorkOps orchestrator.
- **函式**(3):`run_step(eid, extra)` · `pipeline(name, mock_file)` · `main()`
- **CLI**:`--mock-file` `--no-open`
- **自測**:主程式可跑

### VIA_ENG127_WorkopsOutlookGraphConnector
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_outlook_graph_connector`(版本 1;現役 `workops_outlook_graph_connector.py`)
- **功能**:ENG-051 Microsoft Graph Outlook connector.
- **函式**(11):`jload(p, d)` · `atomic(p, o)` · `cache_path(cfg)` · `delta_path(cfg)` · `get_token(cfg, interactive)` · `req(token, url, method, json_body, timeout)` · `list_all_folders(token, cfg)` · `recipients(v)` · `normalized(msg, folder)` · `stable_hash(x)`
- **CLI**:`--body` `--subject` `--to`
- **自測**:主程式可跑

### VIA_ENG128_WorkopsProcessMiningKpiBridge
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_process_mining_kpi_bridge`(版本 1;現役 `workops_process_mining_kpi_bridge.py`)
- **功能**:ENG-045 Process Mining KPI Bridge.
- **函式**(5):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG129_WorkopsProgressEstimator
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_progress_estimator`(版本 1;現役 `workops_progress_estimator.py`)
- **功能**:ENG-049 Evidence-based Project Progress Estimator.
- **函式**(5):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG130_WorkopsProjectCardAggregator
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_project_card_aggregator`(版本 1;現役 `workops_project_card_aggregator.py`)
- **功能**:ENG-038 Project Card Aggregator.
- **函式**(6):`loadj(p, d)` · `loadjl(p)` · `atomic(p, o)` · `latest_projects()` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG131_WorkopsProjectFusion
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_project_fusion`(版本 1;現役 `workops_project_fusion.py`)
- **功能**:ENG-032 Project Fusion Classifier.
- **函式**(12):`loadj(p, d)` · `loadjl(p)` · `readcsv(p)` · `pick(r, names)` · `toks(s)` · `sim(a, b)` · `control_sheet_rows()` · `latest_projects()` · `confirmed_memory()` · `extract_codes(text, pats)`
- **自測**:主程式可跑

### VIA_ENG132_WorkopsProjectHealth
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_project_health`(版本 1;現役 `workops_project_health.py`)
- **功能**:ENG-050 Explainable Project Health + Accuracy Aggregator.
- **函式**(5):`loadj(p, d)` · `atomic(p, o)` · `clamp(x)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG133_WorkopsProjectRegistration
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_project_registration`(版本 1;現役 `workops_project_registration.py`)
- **功能**:ENG-033 Project Registration Engine.
- **函式**(8):`loadjl(p)` · `append(p, obj)` · `current(pid)` · `create(name, aliases, product_codes, folders, stakeholders)` · `rename(pid, name)` · `accept(conv, pid, folder, product_codes)` · `list_projects()` · `main()`
- **CLI**:`--folder` `--product`
- **自測**:主程式可跑

### VIA_ENG134_WorkopsRetentionManager
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_retention_manager`(版本 1;現役 `workops_retention_manager.py`)
- **功能**:ENG-067 Local data-retention planner and explicit apply. Creates backup first.
- **函式**(5):`j(p, d)` · `dt(s)` · `plan()` · `apply(confirm)` · `main()`
- **CLI**:`--confirm`
- **自測**:主程式可跑

### VIA_ENG135_WorkopsSmartEscalation
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_smart_escalation`(版本 1;現役 `workops_smart_escalation.py`)
- **功能**:ENG-064 Smart escalation recommendations only.
- **函式**(3):`j(p, d)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG136_WorkopsSsotStore
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_ssot_store`(版本 1;現役 `workops_ssot_store.py`)
- **功能**:ENG-052 SSOT persistence. Preferred DuckDB + Parquet; SQLite is a degraded local fallback.
- **函式**(10):`jload(p, d)` · `jl(p)` · `csvrows(p)` · `latest_projects()` · `datasets()` · `normalize(rows)` · `duckdb_snapshot(cfg, data)` · `sqlite_snapshot(cfg, data)` · `snapshot()` · `main()`
- **自測**:主程式可跑

### VIA_ENG137_WorkopsStakeholderMatrix
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_stakeholder_matrix`(版本 1;現役 `workops_stakeholder_matrix.py`)
- **功能**:ENG-062 Stakeholder registry + RACI candidates. Role inference is never canonical until confirmed.
- **函式**(10):`jl(p)` · `jload(p, d)` · `append(p, o)` · `confirmed_projects()` · `stakeholder_ids()` · `sid(email, name)` · `confirmed_roles()` · `build()` · `confirm(project_id, stakeholder_id, role)` · `main()`
- **自測**:主程式可跑

### VIA_ENG138_WorkopsTimelineDependency
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_timeline_dependency`(版本 1;現役 `workops_timeline_dependency.py`)
- **功能**:ENG-054 Project timeline reconstruction and dependency impact.
- **函式**(4):`jload(p, d)` · `jl(p)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG139_WorkopsTopicEpisode
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_topic_episode`(版本 1;現役 `workops_topic_episode.py`)
- **功能**:ENG-066 Thread -> new-content -> topic episode reconstruction using CPU-light lexical continuity.
- **函式**(8):`j(p, d)` · `jl(p)` · `strip_quote(text, markers)` · `toks(s)` · `jac(a, b)` · `topic_id(conv, first_graph_id)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG140_WorkopsUnifiedSearch
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_unified_search`(版本 1;現役 `workops_unified_search.py`)
- **功能**:ENG-056 Unified local search across SSOT sidecars.
- **函式**(5):`jload(p, d)` · `jl(p)` · `current_projects()` · `search(q, limit)` · `main()`
- **CLI**:`--limit`
- **自測**:主程式可跑

### VIA_ENG141_WorkopsUnifiedWorkRegister
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_unified_work_register`(版本 1;現役 `workops_unified_work_register.py`)
- **功能**:ENG-053 Unified Work Register: one operational queue across projects.
- **函式**(7):`jload(p, d)` · `jl(p)` · `append(p, o)` · `id_for(kind, source_id, prefix)` · `item(kind, source, prefix, title, project_id)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG142_WorkopsWatchlistPrioritizer
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/engines/workops_watchlist_prioritizer`(版本 1;現役 `workops_watchlist_prioritizer.py`)
- **功能**:無說明(候補)
- **函式**(5):`loadj(p, d)` · `atomic(p, o)` · `score(c, w)` · `build()` · `main()`
- **自測**:主程式可跑

### VIA_ENG143_Candidate
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/out/candidate`(版本 1;現役 `candidate.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VIA_ENG144_RcAcceptance
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/tests/rc_acceptance`(版本 1;現役 `rc_acceptance.py`)
- **功能**:Release Candidate acceptance tests. No network and no Outlook mutation.
- **函式**(2):`run(eng, root, script, timeout)` · `main()`
- **CLI**:`--language` `--no-open`
- **自測**:主程式可跑

### VIA_ENG145_TestEngines
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/tests/test_engines`(版本 1;現役 `test_engines.py`)
- **功能**:無說明(候補)
- **函式**(5):`run(script)` · `reset()` · `test_autocode()` · `test_registration_and_fusion()` · `test_reply_builder()`
- **CLI**:`--folder` `--product`
- **自測**:匯入型

### VIA_ENG146_Test
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/tests/test`(版本 2;現役 `test_v0103.py`)
- **功能**:無說明(候補)
- **函式**(7):`run(script)` · `reset()` · `seed()` · `pipe()` · `test_close()` · `test_watch()` · `test_lifecycle()`
- **CLI**:`--language` `--project-id` `--reason`
- **自測**:匯入型

### VIA_ENG147_TestV0106Accuracy
- **族**:`functional modules/WorkOps/VIA_WorkOps_Product_RC_v0200/tests/test_v0106_accuracy`(版本 1;現役 `test_v0106_accuracy.py`)
- **功能**:無說明(候補)
- **函式**(2):`run(eng, work, script)` · `test_accuracy_hard_gates()`
- **自測**:匯入型


## VRN · 報告情報(60 支)

### VRN_ENG001_ACTIVATEANDCROSSVALIDATE
- **族**:`functional modules/VRN/ACTIVATE_AND_CROSS_VALIDATE`(版本 1;現役 `ACTIVATE_AND_CROSS_VALIDATE.py`)
- **功能**:ACTIVATE_AND_CROSS_VALIDATE.py
- **函式**(2):`run_set(set_name, ocr_overrides, ocr_missing)` · `cv(category, name, ok, va, vb)`
- **CLI**:`--output-dir`
- **自測**:匯入型 · **整合邊**:VIA_HardGate_BootPrecheck

### VRN_ENG002_InvestmentRegexPatternVALIDATED
- **族**:`functional modules/VRN/InvestmentRegexPattern_VALIDATED`(版本 1;現役 `InvestmentRegexPattern_VALIDATED.py`)
- **功能**:╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
- **類**:_FbTimer, _FbHardwareTuner, _FbGCTuner, StatementType, CategoryType, ValidationLevel, PatternDef, ExtractedValue, ValidationResult, InvestmentPatternMatcher, FinancialDataValidator, FinancialStatementAnalyzer
- **函式**(3):`get_version()` · `get_status()` · `run_test()`
- **自測**:主程式可跑

### VRN_ENG003_HardGateBootPrecheck
- **族**:`functional modules/VRN/VIA_HardGate_BootPrecheck`(版本 1;現役 `VIA_HardGate_BootPrecheck.py`)
- **功能**:VIA_HardGate_BootPrecheck.py — 7-Tool BOOT_PRECHECK 統一載入樣板
- **函式**(3):`hardgate_load_inline(ssot_dir, policy, py_inject, quiet)` · `hardgate_caps_summary(caps)` · `hardgate_get(caps, key)`
- **CLI**:`--quiet` `--ssot-dir`
- **自測**:主程式可跑

### VRN_ENG004_VISVRNTableGeometryReconstructor
- **族**:`functional modules/VRN/VIS_VRN_TableGeometryReconstructor`(版本 1;現役 `VIS_VRN_TableGeometryReconstructor_v0101.py`)
- **功能**:VIS_VRN_TableGeometryReconstructor_v0101
- **函式**(12):`def_normalize_space_v0101(x)` · `def_is_route_only_source_v0101(source_file, ticker)` · `def_is_period_or_header_fragment_v0101(account_raw, value_raw)` · `def_find_value_tokens_v0101(x)` · `def_clean_number_v0101(x)` · `def_value_type_v0101(x)` · `def_account_hits_v0101(text)` · `def_split_accounts_v0101(account_raw)` · `def_values_from_account_and_value_v0101(account_raw, value_raw)` · `def_canonical_account_v0101(account)`
- **CLI**:`---`
- **自測**:主程式可跑

### VRN_ENG005_VISVRNTableHeaderPeriodOriginalRestore
- **族**:`functional modules/VRN/VIS_VRN_TableHeaderPeriodOriginalRestore`(版本 1;現役 `VIS_VRN_TableHeaderPeriodOriginalRestore_v0100.py`)
- **功能**:VIS_VRN_TableHeaderPeriodOriginalRestore_v0100
- **函式**(12):`def_clean_space_v0100(x)` · `def_num_tokens_v0100(x)` · `def_is_noise_line_v0100(x)` · `def_has_account_signal_v0100(x)` · `def_period_tokens_v0100(x)` · `def_forward_fill_cells_v0100(cells)` · `def_split_line_to_cells_v0100(line)` · `def_pick_header_lines_v0100(lines, row_index, up_lines)` · `def_restore_from_text_line_v0100(source_file, line_no, raw_line, context_lines, up_lines)` · `def_restore_from_pdfplumber_table_row_v0100(source_file, page, table_index, row_index, raw_cells)`
- **自測**:主程式可跑

### VRN_ENG006_CompleteOCREngineRegistry
- **族**:`functional modules/VRN/VRN_Complete_OCR_Engine_Registry`(版本 1;現役 `VRN_Complete_OCR_Engine_Registry.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
- **類**:EngineType, EngineStatus, UsageLimit, EngineInfo, OCREngineBase, TesseractEngine, EasyOCREngine, RapidOCREngine, PaddleOCREngine, StubEngine, OCRManager, OCRValidator
- **函式**(2):`create_engine(engine_id)` · `main()`
- **CLI**:`--audit` `--init` `--json` `--lang` `--ocr` `--status` `--test`
- **自測**:主程式可跑

### VRN_ENG007_FinalizeCoreV21
- **族**:`functional modules/VRN/VRN_Finalize_Core_v2_1`(版本 1;現役 `VRN_Finalize_Core_v2_1.py`)
- **功能**:VRN Finalize AIO - embedded Python core
- **函式**(3):`cmd_anchor_preview(canonical_master, out_json)` · `cmd_append_patch(canonical_master, policy_module, backup_dir, out_json)` · `cmd_post_validate(canonical_master, out_json)`
- **自測**:主程式可跑

### VRN_ENG008_HealthCheck
- **族**:`functional modules/VRN/VRN_HealthCheck`(版本 1;現役 `VRN_HealthCheck.py`)
- **功能**:VRN_HealthCheck.py — 生產資料夾健檢
- **函式**(2):`run_healthcheck(vrn_dir, quiet)` · `build_html_report(summary)`
- **CLI**:`--no-html` `--quiet` `--vrn-dir`
- **自測**:主程式可跑

### VRN_ENG009_M03ChineseOCRLEGOUltra
- **族**:`functional modules/VRN/VRN_M03_Chinese_OCR_LEGO_Ultra`(版本 2;現役 `VRN_M03_Chinese_OCR_LEGO_Ultra_v22.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:KPIMetric, OCRResult, ProcessingStats, SmartDeskewer, ChineseConverter, OCREngine, PaddleOCREngine, EasyOCREngine, TesseractEngine, RapidOCREngine, CnOCREngine, SimulatedOCREngine
- **函式**(4):`get_engine(output_dir)` · `health_check()` · `selftest()` · `main()`
- **CLI**:`--engine` `--health` `--input` `--input_dir` `--output` `--output_dir` `--self-test` `--verbose`
- **自測**:主程式可跑

### VRN_ENG010_M03LayoutOCRUltra
- **族**:`functional modules/VRN/VRN_M03_Layout_OCR_Ultra`(版本 1;現役 `VRN_M03_Layout_OCR_Ultra.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:BoundingBox, OCRElement, PageLayout, BaseOCREngine, PaddleOCREngine, EasyOCREngine, TesseractEngine, OpenCVEngine, StubEngine, LayoutOCREngine
- **函式**(4):`module_meta()` · `run(cfg, ctx)` · `self_test()` · `health_check()`
- **CLI**:`--engine` `--health` `--ocr` `--output` `--test`
- **自測**:主程式可跑

### VRN_ENG011_M03TIFFOCRUltra
- **族**:`functional modules/VRN/VRN_M03_TIFF_OCR_Ultra`(版本 1;現役 `VRN_M03_TIFF_OCR_Ultra.py`)
- **功能**:╔═══════════════════════════════════════════════════════════════════════════════════════════╗
- **類**:OCREngine, LayoutEngine, BlockType, ProcessingStatus, BoundingBox, OCRResult, LayoutBlock, TIFFMetadata, FrameResult, DocumentResult, AcceleratorEngine, TIFFProcessor
- **函式**(5):`CONFIG()` · `log(level, msg)` · `health_check()` · `run_selftest()` · `main()`
- **CLI**:`--engine` `--frames` `--health` `--layout` `--out-dir` `--selftest` `--tiff` `--version`
- **自測**:✅ --selftest

### VRN_ENG012_M04OCRPostProcessorLEGOUltra
- **族**:`functional modules/VRN/VRN_M04_OCR_PostProcessor_LEGO_Ultra`(版本 1;現役 `VRN_M04_OCR_PostProcessor_LEGO_Ultra.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:ExtractedPrice, ExtractedDate, ExtractedTable, PostProcessResult, ProcessingStats, PriceExtractor, DateExtractor, TableExtractor, TextCleaner, M04Processor
- **函式**(1):`main()`
- **CLI**:`--input` `--input_dir` `--output` `--output_dir` `--verbose`
- **自測**:主程式可跑

### VRN_ENG013_MDL001Converter
- **族**:`functional modules/VRN/VRN_MDL001_Converter`(版本 1;現役 `VRN_MDL001_Converter.py`)
- **功能**:無說明(候補)
- **類**:MDL001DBWriter, MDL001BatchBuffer, MDL001DuckWriter, MDL001SelfVerifier, VRN_MDL001_Converter
- **函式**(5):`file_sha256(path)` · `detect_input_type(path)` · `list_input_files(input_dir)` · `parse_filename_meta(filename)` · `convert_pdf_to_hq_pdf(src_path, dst_path, dpi, jpeg_quality, max_pages)`
- **CLI**:`--convert-to` `--headless` `--outdir`
- **自測**:主程式可跑

### VRN_ENG014_MDL001StockReportPipeline
- **族**:`functional modules/VRN/VRN_MDL001_StockReportPipeline`(版本 1;現役 `VRN_MDL001_StockReportPipeline.py`)
- **功能**:無說明(候補)
- **類**:MDL001SPDocCache, GCTuner, MemoryPool, HardwareGovernor, VIACache, LessonLearnedDB, SentenceRepairEngine, TextRepairEngine, FinancialRow, VRNDBWriter, MDL001SPBatchBuffer, MDL001SPDuckWriter
- **函式**(3):`mkdir(p)` · `trim(s)` · `san(n)`
- **CLI**:`--accel` `--batch` `--db` `--dpi` `--in_dir` `--no_cache` `--no_gov` `--out_dir` `--pdf_temp` `--workers`
- **自測**:主程式可跑 · **整合邊**:VeritasAegisNexus, VeritasCeleritas

### VRN_ENG015_MDL002LayoutExtractor
- **族**:`functional modules/VRN/VRN_MDL002_LayoutExtractor`(版本 1;現役 `VRN_MDL002_LayoutExtractor.py`)
- **功能**:無說明(候補)
- **類**:TableRecord, TextBlock, MDL002DocCache, MDL002DBWriter, MDL002BatchBuffer, MDL002DuckWriter, MDL002SelfVerifier, VRN_MDL002_LayoutExtractor
- **函式**(5):`list_pdfs_in_temp(pdf_temp)` · `classify_page(page_text, page_no)` · `extract_zones_first_page(pdf_path, page, cfg)` · `detect_table_regions(pdf_path, page_no, page_text, page_cls, cfg)` · `split_quadrants(pdf_path, page_no, cfg, doc_cache)`
- **自測**:主程式可跑

### VRN_ENG016_MDL003TableRestorer
- **族**:`functional modules/VRN/VRN_MDL003_TableRestorer`(版本 1;現役 `VRN_MDL003_TableRestorer.py`)
- **功能**:無說明(候補)
- **類**:TextRepairEngine, RestoredTable, MDL003BatchBuffer, MDL003DuckWriter, MDL003DBWriter, MDL003SelfVerifier, VRN_MDL003_TableRestorer
- **函式**(4):`load_mdl002_output(mdl002_temp)` · `repair_text_blocks_batch(blocks, reflow)` · `canonicalize_label(label)` · `classify_fin_type(canonical)`
- **CLI**:`---`
- **自測**:主程式可跑

### VRN_ENG017_MDL004OCRFetchingPDFTable
- **族**:`functional modules/VRN/VRN_MDL004_OCR_FetchingPDFTable`(版本 1;現役 `VRN_MDL004_OCR_FetchingPDFTable.py`)
- **功能**:無說明(候補)
- **類**:MDL004DocCache, RawTableResult, FixedTable, MDL004DBWriter, MDL004BatchBuffer, MDL004DuckWriter, MDL004SelfVerifier, VRN_MDL004_OCRFetcher
- **函式**(3):`list_pdfs(pdf_temp)` · `is_scan_pdf(pdf_path)` · `get_header_context(page, table_bbox)`
- **CLI**:`---` `--dpi` `--engine-primary` `--engine-secondary` `--mdl004-temp` `--no-db` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑

### VRN_ENG018_MDL005OCRFetchingPDFText
- **族**:`functional modules/VRN/VRN_MDL005_OCRFetchingPDFText`(版本 1;現役 `VRN_MDL005_OCRFetchingPDFText.py`)
- **功能**:無說明(候補)
- **類**:MDL005DocCache, RawTextBlock, FixedTextBlock, MDL005DBWriter, MDL005BatchBuffer, MDL005DuckWriter, MDL005SelfVerifier, VRN_MDL005_TextFetcher
- **函式**(2):`normalize_rating(raw)` · `load_plugins(ssot_dir)`
- **CLI**:`--engine-primary` `--engine-secondary` `--mdl005-temp` `--no-aegis` `--no-celeritas` `--no-db` `--no-ssot` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑

### VRN_ENG019_MDL006ConsolidatorAndPhaseValidator
- **族**:`functional modules/VRN/VRN_MDL006_ConsolidatorAndPhaseValidator`(版本 1;現役 `VRN_MDL006_ConsolidatorAndPhaseValidator.py`)
- **功能**:無說明(候補)
- **類**:CompareResult, MDL006BatchBuffer, MDL006DuckWriter, MDL006SelfVerifier, VRN_MDL006_Consolidator
- **函式**(2):`load_mdl003_output(mdl003_temp)` · `load_mdl004_output(mdl004_temp)`
- **自測**:匯入型

### VRN_ENG020_MDL007APIDataFetcher
- **族**:`functional modules/VRN/VRN_MDL007_APIDataFetcher`(版本 1;現役 `VRN_MDL007_APIDataFetcher.py`)
- **功能**:無說明(候補)
- **類**:MDL007DBWriter, MDL007BatchBuffer, MDL007DuckWriter, MDL007SelfVerifier, VRN_MDL007_APIDataFetcher
- **函式**(4):`load_plugins(ssot_dir)` · `normalize_to_million(value, source_unit)` · `normalize_precision(value_million, decimal)` · `norm(value, source_unit)`
- **CLI**:`--mdl007-temp` `--ssot-dir` `--tickers` `--workers`
- **自測**:主程式可跑

### VRN_ENG021_MDL008CrossValidator
- **族**:`functional modules/VRN/VRN_MDL008_CrossValidator`(版本 1;現役 `VRN_MDL008_CrossValidator.py`)
- **功能**:無說明(候補)
- **類**:VerifyResult, ForecastCheck, MDL008DBWriter, MDL008BatchBuffer, MDL008DuckWriter, MDL008SelfVerifier, VRN_MDL008_CrossValidator
- **函式**(7):`is_historical(period)` · `is_forecast(period)` · `to_year(period)` · `load_plugins(ssot_dir)` · `to_million(value, unit)` · `precision_normalize(v, decimal)` · `std_val(value, unit)`
- **CLI**:`--api-parquet` `--output-dir` `--report-parquet` `--ssot-dir`
- **自測**:主程式可跑

### VRN_ENG022_MDL010CodeRegistry
- **族**:`functional modules/VRN/VRN_MDL010_CodeRegistry`(版本 1;現役 `VRN_MDL010_CodeRegistry.py`)
- **功能**:無說明(候補)
- **類**:VRN_MDL010_CodeRegistry
- **CLI**:`--out` `--query`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified, VeritasAegisNexus, VeritasCeleritas

### VRN_ENG023_MDL011DailyFetcher
- **族**:`functional modules/VRN/VRN_MDL011_DailyFetcher`(版本 1;現役 `VRN_MDL011_DailyFetcher.py`)
- **功能**:無說明(候補)
- **類**:VRN_MDL011_DailyFetcher
- **CLI**:`--codes` `--date` `--out`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified, VeritasAegisNexus, VeritasCeleritas

### VRN_ENG024_MDL239VrnNewReportFormatSystemDefaultInstallerV06155REPORTV06155
- **族**:`functional modules/VRN/VRN_MDL239_vrn_new_report_format_system_default_installer_v06155__REPORT__v06155`(版本 1;現役 `VRN_MDL239_vrn_new_report_format_system_default_installer_v06155__REPORT__v06155.py`)
- **功能**:無說明(候補)
- **函式**(11):`def_now()` · `def_sha256(path)` · `def_backup_if_exists(path, tag)` · `def_write_text(path, text)` · `def_write_json(path, obj)` · `def_light(sev)` · `def_gate_module_code()` · `def_registry_obj()` · `def_playbook_text()` · `def_write_html_report(path, rows, registry)`
- **自測**:主程式可跑

### VRN_ENG025_MDL259VrnReportDateWindowTableRestoreV0597REPORT
- **族**:`functional modules/VRN/VRN_MDL259_vrn_report_date_window_table_restore_v0597__REPORT_`(版本 1;現役 `VRN_MDL259_vrn_report_date_window_table_restore_v0597__REPORT__v0597.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_config()` · `def_now()` · `def_h(x)` · `def_nonblank(x)` · `def_clean(x)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_first(row, keys)` · `def_norm_filename(x)`
- **自測**:主程式可跑

### VRN_ENG026_OCRPostProcessingValidationSystem
- **族**:`functional modules/VRN/VRN_OCR_PostProcessing_Validation_System`(版本 1;現役 `VRN_OCR_PostProcessing_Validation_System.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
- **類**:DataType, ValidationStatus, ValidationResult, PostProcessingResult, PatternLibrary, TextNormalizer, Validator, VeritasSynonymEngine, OCRPostProcessor
- **函式**(2):`run_tests()` · `main()`
- **CLI**:`--json` `--process` `--test`
- **自測**:主程式可跑

### VRN_ENG027_PipelineRunner
- **族**:`functional modules/VRN/VRN_Pipeline_Runner`(版本 1;現役 `VRN_Pipeline_Runner.py`)
- **功能**:VRN_Pipeline_Runner.py — 生產管線 runner(v0100R 重建;README 載明「delegates to above」,
- **函式**(1):`run()`
- **CLI**:`--no-html` `--no-pause` `--quiet` `--vrn-dir`
- **自測**:主程式可跑

### VRN_ENG028_SmokeTest
- **族**:`functional modules/VRN/VRN_SmokeTest`(版本 1;現役 `VRN_SmokeTest.py`)
- **功能**:VRN_SmokeTest.py — 部署後快速煙霧測試(v0100R 重建;README 目錄載明本檔,工作站正本候上傳到件即讓位)。
- **函式**(1):`run()`
- **CLI**:`--no-pause`
- **自測**:主程式可跑

### VRN_ENG029_EditableLegacy
- **族**:`functional modules/VRN/_quarantine_pip_vendor/editable_legacy`(版本 1;現役 `editable_legacy.py`)
- **功能**:Legacy editable installation process, i.e. `setup.py develop`.
- **函式**(1):`install_editable(global_options, prefix, home, use_user_site, name)`
- **自測**:匯入型

### VRN_ENG030_InstallationReport
- **族**:`functional modules/VRN/_quarantine_pip_vendor/installation_report`(版本 1;現役 `installation_report.py`)
- **功能**:無說明(候補)
- **類**:InstallationReport
- **自測**:匯入型

### VRN_ENG031_MetadataEditable
- **族**:`functional modules/VRN/_quarantine_pip_vendor/metadata_editable`(版本 1;現役 `metadata_editable.py`)
- **功能**:Metadata generation logic for source distributions.
- **函式**(1):`generate_editable_metadata(build_env, backend, details)`
- **自測**:匯入型

### VRN_ENG032_Reporter
- **族**:`functional modules/VRN/_quarantine_pip_vendor/reporter`(版本 1;現役 `reporter.py`)
- **功能**:無說明(候補)
- **類**:PipReporter, PipDebuggingReporter
- **自測**:匯入型

### VRN_ENG033_Reporters
- **族**:`functional modules/VRN/_quarantine_pip_vendor/reporters`(版本 1;現役 `reporters.py`)
- **功能**:無說明(候補)
- **類**:BaseReporter
- **自測**:匯入型

### VRN_ENG034_Table
- **族**:`functional modules/VRN/_quarantine_pip_vendor/table`(版本 1;現役 `table.py`)
- **功能**:無說明(候補)
- **類**:Column, Row, _Cell, Table
- **自測**:主程式可跑

### VRN_ENG035_WheelEditable
- **族**:`functional modules/VRN/_quarantine_pip_vendor/wheel_editable`(版本 1;現役 `wheel_editable.py`)
- **功能**:無說明(候補)
- **函式**(1):`build_wheel_editable(name, backend, metadata_directory, tempd)`
- **自測**:匯入型

### VRN_ENG036_FinalizeCoreV2
- **族**:`functional modules/VRN/_superseded/20260804/VRN_Finalize_Core_v2`(版本 1;現役 `VRN_Finalize_Core_v2.py`)
- **功能**:VRN Finalize AIO - embedded Python core
- **函式**(3):`cmd_anchor_preview(canonical_master, out_json)` · `cmd_append_patch(canonical_master, policy_module, backup_dir, out_json)` · `cmd_post_validate(canonical_master, out_json)`
- **自測**:主程式可跑

### VRN_ENG037_MDL001Converter
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL001_Converter`(版本 1;現役 `VRN_MDL001_Converter.py`)
- **功能**:無說明(候補)
- **類**:MDL001DBWriter, VRN_MDL001_Converter
- **函式**(5):`file_sha256(path)` · `detect_input_type(path)` · `list_input_files(input_dir)` · `parse_filename_meta(filename)` · `convert_pdf_to_hq_pdf(src_path, dst_path, dpi, jpeg_quality, max_pages)`
- **CLI**:`--convert-to` `--headless` `--outdir`
- **自測**:主程式可跑

### VRN_ENG038_MDL002LayoutExtractor
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL002_LayoutExtractor`(版本 1;現役 `VRN_MDL002_LayoutExtractor.py`)
- **功能**:無說明(候補)
- **類**:TableRecord, TextBlock, MDL002DBWriter, VRN_MDL002_LayoutExtractor
- **函式**(5):`list_pdfs_in_temp(pdf_temp)` · `classify_page(page_text, page_no)` · `extract_zones_first_page(pdf_path, page, cfg)` · `detect_table_regions(pdf_path, page_no, page_text, page_cls, cfg)` · `split_quadrants(pdf_path, page_no, cfg)`
- **自測**:主程式可跑

### VRN_ENG039_MDL003TableRestorer
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL003_TableRestorer`(版本 1;現役 `VRN_MDL003_TableRestorer.py`)
- **功能**:無說明(候補)
- **類**:TextRepairEngine, RestoredTable, MDL003DBWriter, VRN_MDL003_TableRestorer
- **函式**(7):`load_mdl002_output(mdl002_temp)` · `canonicalize_label(label)` · `classify_fin_type(canonical)` · `clean_ocr_number(val)` · `is_axis_noise(text)` · `restore_one_table(tbl_dict, repair, cfg)` · `apply_calc_rules(rt)`
- **CLI**:`---`
- **自測**:主程式可跑

### VRN_ENG040_MDL004OCRFetchingPDFTableV1
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL004_OCR_FetchingPDFTable_v1`(版本 1;現役 `VRN_MDL004_OCR_FetchingPDFTable_v1.py`)
- **功能**:無說明(候補)
- **類**:RawTableResult, FixedTable, MDL004DBWriter, VRN_MDL004_OCRFetcher
- **函式**(3):`list_pdfs(pdf_temp)` · `is_scan_pdf(pdf_path)` · `get_header_context(page, table_bbox)`
- **CLI**:`---` `--dpi` `--engine-primary` `--engine-secondary` `--mdl004-temp` `--no-db` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑

### VRN_ENG041_MDL005OCRFetchingPDFTextV1
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL005_OCRFetchingPDFText_v1`(版本 1;現役 `VRN_MDL005_OCRFetchingPDFText_v1.py`)
- **功能**:無說明(候補)
- **類**:RawTextBlock, FixedTextBlock, MDL005DBWriter, VRN_MDL005_TextFetcher
- **函式**(2):`normalize_rating(raw)` · `load_plugins(ssot_dir)`
- **CLI**:`--engine-primary` `--engine-secondary` `--mdl005-temp` `--no-aegis` `--no-celeritas` `--no-db` `--no-ssot` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑

### VRN_ENG042_MDL006ConsolidatorAndPhaseValidator
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL006_ConsolidatorAndPhaseValidator`(版本 1;現役 `VRN_MDL006_ConsolidatorAndPhaseValidator.py`)
- **功能**:無說明(候補)
- **類**:CompareResult, VRN_MDL006_Consolidator
- **函式**(2):`load_mdl003_output(mdl003_temp)` · `load_mdl004_output(mdl004_temp)`
- **自測**:匯入型

### VRN_ENG043_MDL007APIDataFetcher
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL007_APIDataFetcher`(版本 1;現役 `VRN_MDL007_APIDataFetcher.py`)
- **功能**:無說明(候補)
- **類**:MDL007DBWriter, VRN_MDL007_APIDataFetcher
- **函式**(4):`load_plugins(ssot_dir)` · `normalize_to_million(value, source_unit)` · `normalize_precision(value_million, decimal)` · `norm(value, source_unit)`
- **CLI**:`--mdl007-temp` `--ssot-dir` `--tickers` `--workers`
- **自測**:主程式可跑

### VRN_ENG044_MDL008CrossValidator
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL008_CrossValidator`(版本 1;現役 `VRN_MDL008_CrossValidator.py`)
- **功能**:無說明(候補)
- **類**:VerifyResult, ForecastCheck, MDL008DBWriter, VRN_MDL008_CrossValidator
- **函式**(7):`is_historical(period)` · `is_forecast(period)` · `to_year(period)` · `load_plugins(ssot_dir)` · `to_million(value, unit)` · `precision_normalize(v, decimal)` · `std_val(value, unit)`
- **CLI**:`--api-parquet` `--output-dir` `--report-parquet` `--ssot-dir`
- **自測**:主程式可跑

### VRN_ENG045_PanoramaXcheck
- **族**:`functional modules/VRN/panorama_xcheck`(版本 3;現役 `panorama_xcheck_v112.py`)
- **功能**:panorama_xcheck_v110.py — 全景交叉核對(v111R 重建;README 載明「full 8-module dataflow」
- **函式**(1):`run()`
- **CLI**:`--no-pause`
- **自測**:主程式可跑

### VRN_ENG046_ContentExtractCandidate
- **族**:`functional modules/VRN/vrn_content_extract_candidate`(版本 1;現役 `vrn_content_extract_candidate_v0100.py`)
- **功能**:無說明(候補)
- **函式**(2):`extract_text(path, max_pages)` · `main(argv)`
- **CLI**:`--commit` `--limit`
- **自測**:主程式可跑

### VRN_ENG047_ContentExtract
- **族**:`functional modules/VRN/vrn_content_extract`(版本 1;現役 `vrn_content_extract_v0101.py`)
- **功能**:無說明(候補)
- **函式**(3):`parse_meta(fname)` · `extract_text(path, max_pages)` · `main(argv)`
- **CLI**:`--commit` `--limit`
- **自測**:主程式可跑

### VRN_ENG048_ContentProbe
- **族**:`functional modules/VRN/vrn_content_probe`(版本 1;現役 `vrn_content_probe_v0100.py`)
- **功能**:無說明(候補)
- **函式**(2):`extract_text(path, max_pages)` · `main(argv)`
- **CLI**:`--limit` `--no-open`
- **自測**:主程式可跑

### VRN_ENG049_ContentReconcile
- **族**:`functional modules/VRN/vrn_content_reconcile`(版本 2;現役 `vrn_content_reconcile_v0101.py`)
- **功能**:vrn_content_reconcile_v0101 — OCR 擷取產物 × SSOT v2 內容級對帳(唯讀;缺口診斷版)
- **函式**(3):`load_flat(base, stem)` · `norm(name)` · `main()`
- **CLI**:`--json` `--no-open` `--staging`
- **自測**:主程式可跑

### VRN_ENG050_ContentStore
- **族**:`functional modules/VRN/vrn_content_store`(版本 7;現役 `vrn_content_store_v0106.py`)
- **功能**:vrn_content_store_v0106 — 對帳綠燈內容落庫 via.duckdb(Windows 自鎖根因修)
- **函式**(2):`find_db(override)` · `main()`
- **CLI**:`--commit` `--db` `--init` `--migrate` `--purge-onedrive`
- **自測**:主程式可跑

### VRN_ENG051_D8bFilenameParser
- **族**:`functional modules/VRN/vrn_d8b_filename_parser`(版本 1;現役 `vrn_d8b_filename_parser.py`)
- **功能**:無說明(候補)
- **函式**(3):`parse_filename(fn)` · `classify_eps(text)` · `validate_eps_pair(basic, diluted, tol)`
- **自測**:匯入型

### VRN_ENG052_DocxEngine
- **族**:`functional modules/VRN/vrn_docx_engine`(版本 2;現役 `vrn_docx_engine_v0101.py`)
- **功能**:vrn_docx_engine_v0101 — DOCX 深度解析引擎(10 地雷硬化版)
- **函式**(10):`precheck_zip(path)` · `flatten_cell(cell)` · `strip_ghost(text)` · `extract_builtin_xml(path)` · `extract_docx(path)` · `clean_text(text)` · `repair_table(rows)` · `validate_table(tb)` · `compare_docs(old, new)` · `main()`
- **CLI**:`----media/.*?----` `--compare`
- **自測**:主程式可跑

### VRN_ENG053_DocxMerge
- **族**:`functional modules/VRN/vrn_docx_merge`(版本 1;現役 `vrn_docx_merge_v0100.py`)
- **功能**:vrn_docx_merge_v0100 — DOCX 產物併主表(補齊令 2026-08-12)
- **函式**(1):`main()`
- **CLI**:`--commit`
- **自測**:主程式可跑

### VRN_ENG054_InputMatrixValidator
- **族**:`functional modules/VRN/vrn_input_matrix_validator`(版本 3;現役 `vrn_input_matrix_validator_v0102.py`)
- **功能**:vrn_input_matrix_validator_v0102.py — VRN 輸入矩陣驗證引擎 v0102(二進位修正版)。
- **函式**(4):`sniff(path)` · `classify(info)` · `key_cells(rows, heads)` · `main(argv)`
- **CLI**:`--out`
- **自測**:主程式可跑

### VRN_ENG055_OfficeMerge
- **族**:`functional modules/VRN/vrn_office_merge`(版本 2;現役 `vrn_office_merge_v0101.py`)
- **功能**:vrn_office_merge_v0101 — Office(xlsx/csv/docx)併主表橋(TOOL-044)
- **函式**(1):`main()`
- **CLI**:`--commit`
- **自測**:主程式可跑 · **整合邊**:superextract

### VRN_ENG056_PdfForensics
- **族**:`functional modules/VRN/vrn_pdf_forensics`(版本 1;現役 `vrn_pdf_forensics_v0100.py`)
- **功能**:vrn_pdf_forensics_v0100 — PDF 法醫探針(唯讀;零輸出檔死因判定)
- **函式**(2):`forensics(p)` · `main()`
- **CLI**:`--file`
- **自測**:主程式可跑

### VRN_ENG057_ScanOcrRescue
- **族**:`functional modules/VRN/vrn_scan_ocr_rescue`(版本 5;現役 `vrn_scan_ocr_rescue_v0104.py`)
- **功能**:vrn_scan_ocr_rescue_v0104 — 純影像掃描件 OCR 救援(mobile 模型加速版)
- **函式**(1):`main()`
- **CLI**:`--dpi` `--dry-run` `--server`
- **自測**:主程式可跑

### VRN_ENG058_TableOmni
- **族**:`functional modules/VRN/vrn_table_omni`(版本 6;現役 `vrn_table_omni_v0105.py`)
- **功能**:vrn_table_omni_v0105 — 本地免費表格函式庫統包引擎(TOOL-029)
- **類**:_ConsentGate
- **CLI**:`--dpi` `--engines` `--extract` `--pages` `--pdf` `--run-dir` `--selftest` `--timeout` `--worker`
- **自測**:✅ --selftest

### VRN_ENG059_GapMultirescue
- **族**:`functional modules/VRN/vrn_gap_multirescue`(版本 1;現役 `vrn_gap_multirescue_v0100.py`)
- **功能**:vrn_gap_multirescue_v0100 — 表格缺口多方案總攻指揮(TOOL-049;操作員令 2026-08-18)
- **函式**(9):`newest(pattern, root)` · `find_gaps()` · `locate(name)` · `run_stream(argv, timeout)` · `probe_extract_result(name)` · `assault_pdf(name, path, log)` · `assault_docx(name, path, commit, log)` · `selftest()` · `main()`
- **CLI**:`--commit` `--engines` `--extract` `--only` `--selftest` `--timeout`
- **自測**:✅ --selftest · **整合邊**:superextract

### VRN_ENG060_TextOmni
- **族**:`functional modules/VRN/vrn_text_omni`(版本 1;現役 `vrn_text_omni_v0100.py`)
- **功能**:vrn_text_omni_v0100 — 文字統包引擎(TOOL-050;操作員令 2026-08-18)
- **函式**(5):`lanes()` · `guard_zipbomb(p)` · `guard_encrypted(p)` · `mojibake_score(text)` · `extract_one(p)`
- **CLI**:`--extract` `--selftest`
- **自測**:✅ --selftest · **整合邊**:superextract
